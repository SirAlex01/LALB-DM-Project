import re
from collections import defaultdict
import json
import matplotlib.pyplot as plt
import os
import shutil
# Setup output directory for plots
plot_dir = "plots"
if os.path.exists(plot_dir):
    shutil.rmtree(plot_dir)  # Delete the entire directory and its contents
os.makedirs(plot_dir)  # Recreate the empty directory

log_file_path = "log"  # Replace with your actual log path
step = 10  # Desired step between epochs
round_len = 100  # Epochs per round

# Regex patterns
epoch_re = re.compile(r"Epoch:\s*(\d+)")
score_line_re = re.compile(
    r"\|\s*transliterated_linear_b\s*\|\s*greek\s*\|\s*(\w+)\s*\|\s*(None|True|False)\s*\|\s*(None|\d+)\s*\|\s*(train|validation|test|all)\s*\|\s*(\d+)/(\d+)=([\d\.]+)\s*\|?"
)
loss_table_line = re.compile(
    r"\|\s*(loss|nll_loss|reg_loss)\s*\|\s*[\d\.e\+\-]+?\s*\|\s*[\d\.N/Ae\+\-]+?\s*\|\s*([\d\.]+)"
)

def find_init_line(lines, step=step):
    runs = [0]
    last_epoch = 0
    idx = 0
    runs_line_indices = [0]
    for i, line in enumerate(lines):
        match = epoch_re.search(line)
        if match:
            epoch = int(match.group(1))
            if epoch != last_epoch and epoch - last_epoch == step:
                runs[idx] += 1
            elif epoch != last_epoch:
                idx += 1
                runs.append(1)
                runs_line_indices.append(i)
            last_epoch = epoch
    argmax_run = max(range(len(runs)), key=lambda i: (runs[i], i))
    init_line = runs_line_indices[argmax_run]
    return init_line, None if argmax_run == len(runs) - 1 else runs_line_indices[argmax_run + 1]

def collect_metrics_from_logs(log_file_path, step=10, round_len=100):
    # Clean ANSI sequences
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    with open(log_file_path, 'r', encoding='utf-8') as f:
        lines = [ansi_escape.sub('', line) for line in f]


    l, r = find_init_line(lines)
    if r is None:
        r = len(lines)

    # --- Parse logs and build metrics dictionary ---
    metrics = defaultdict(dict)
    seen_epochs = set()
    line_idx = l

    while line_idx < r:
        line = lines[line_idx]
        match = epoch_re.search(line)

        if match:
            current_epoch = int(match.group(1))
            if current_epoch in seen_epochs:
                line_idx += 1
                continue

            seen_epochs.add(current_epoch)
            round_num = (current_epoch - 1) // round_len
            epoch_metrics = {'loss': {}}

            block = lines[line_idx:line_idx + 50]

            # --- Parse accuracy metrics ---
            for bline in block:
                score_match = score_line_re.search(bline)
                if score_match:
                    mode, edit, capacity, split, correct, total, score_val = score_match.groups()
                    key = (mode, edit)
                    if key not in epoch_metrics:
                        epoch_metrics[key] = {"accuracy": {}}
                    epoch_metrics[key]["accuracy"][split] = float(score_val)

            # --- Parse loss metrics from table (mean only) ---
            for bline in block:
                loss_match = loss_table_line.search(bline)
                if loss_match:
                    loss_type, mean_val = loss_match.groups()
                    epoch_metrics["loss"][loss_type] = float(mean_val)

            metrics[round_num][current_epoch] = epoch_metrics

        line_idx += 1
    return metrics

def summarize_metrics(metrics):
    round_summaries = {}

    for round_num, epochs in metrics.items():
        epoch_numbers = sorted(epochs.keys())
        if not epoch_numbers:
            continue

        summary = {
            "average": defaultdict(lambda: defaultdict(float)),
            "final": {}
        }
        count = defaultdict(lambda: defaultdict(int))

        for epoch in epoch_numbers:
            data = epochs[epoch]
            # Loss
            for loss_key, val in data.get("loss", {}).items():
                summary["average"]["loss"][loss_key] += val
                count["loss"][loss_key] += 1

            # Accuracy
            for key in data:
                if key == "loss":
                    continue
                for split, acc in data[key].get("accuracy", {}).items():
                    summary["average"][key][split] += acc
                    count[key][split] += 1

        # Compute average
        for key in summary["average"]:
            for subkey in summary["average"][key]:
                summary["average"][key][subkey] /= count[key][subkey]

        # Final epoch
        summary["final"] = epochs[epoch_numbers[-1]]
        round_summaries[round_num] = summary

    return round_summaries

metrics = collect_metrics_from_logs(log_file_path)
summary = summarize_metrics(metrics)



def plot_metrics(metrics, choice):
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    x = []

    if choice == "loss":
        loss = []
        reg_loss = []
        nll_loss = []

        for round_num, epoch_data in metrics.items():
            for epoch, data in epoch_data.items():
                x.append(epoch)
                loss_data = data['loss']
                loss.append(loss_data.get('loss'))
                reg_loss.append(loss_data.get('reg_loss'))
                nll_loss.append(loss_data.get('nll_loss'))

        # --- Plot all losses together ---
        plt.figure()
        plt.plot(x, loss, label='Total Loss')#, marker='o')
        plt.plot(x, reg_loss, label='Regularization Loss')#, marker='s')
        plt.plot(x, nll_loss, label='NLL Loss')#, marker='^')
        plt.xlabel("Epoch")
        plt.ylabel("Loss Value")
        plt.title("Loss Metrics Over Epochs")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, "loss_all_metrics.png"))
        plt.close()

        # --- Plot each loss separately ---
        loss_components = [
            ('Total Loss', loss, 'loss_total.png', colors[0]),
            ('Regularization Loss', reg_loss, 'loss_regularization.png', colors[1]),
            ('NLL Loss', nll_loss, 'loss_nll.png', colors[2]),
        ]

        for title, values, filename, color in loss_components:
            plt.figure()
            plt.plot(x, values, label=title, color=color)
            plt.xlabel("Epoch")
            plt.ylabel("Loss Value")
            plt.title(f"{title} Over Epochs")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(plot_dir, filename))
            plt.close()


    elif choice == "accuracy":
        modes = [('mle', 'None'), ('flow', 'True'), ('flow', 'False')]
        eval_mode ='train' in metrics[0][10][modes[0]]['accuracy']
        accuracy = defaultdict(lambda: defaultdict(list)) if eval_mode else defaultdict(list)
        mode_names = ['MLE Mode', 'Flow Mode with edit', 'Flow Mode without edit']
        for round_num, epoch_data in metrics.items():
            for epoch, data in epoch_data.items():
                x.append(epoch)
                for mode in modes:
                    accuracy_data = data[mode]['accuracy']
                    if eval_mode:
                        for split, acc in accuracy_data.items():
                            accuracy[mode][split].append(acc)
                    else:
                        accuracy[mode].append(accuracy_data['all'])

        if eval_mode:
            for idx, mode in enumerate(modes):
                mode_label = mode_names[idx]
                mode_tag = mode_label.lower().replace(" ", "_").replace("with_", "with_").replace("without_", "without_")

                # Individual plots per split
                for split_idx, split in enumerate(['train', 'validation', 'test']):
                    plt.figure()
                    plt.plot(x, accuracy[mode][split], label=f'{split.capitalize()} Accuracy',
                             color=colors[split_idx])
                    plt.xlabel("Epoch")
                    plt.ylabel("Accuracy")
                    plt.title(f'{mode_label} - {split.capitalize()} Accuracy')
                    plt.grid(True)
                    plt.legend()
                    plt.tight_layout()
                    plt.savefig(os.path.join(plot_dir, f"accuracy_{mode_tag}_{split}.png"))
                    plt.close()

                # Combined plot with all splits
                plt.figure()
                for split_idx, split in enumerate(['train', 'validation', 'test']):
                    plt.plot(x, accuracy[mode][split], label=f'{split.capitalize()} Accuracy',
                             color=colors[split_idx])
                plt.xlabel("Epoch")
                plt.ylabel("Accuracy")
                plt.title(f'{mode_label} - All Splits')
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(plot_dir, f"accuracy_{mode_tag}_all_splits.png"))
                plt.close()

            # ✅ Combined mode plot per split (all 3 modes, for one split)
            for split_idx, split in enumerate(['train', 'validation', 'test']):
                plt.figure()
                for idx, mode in enumerate(modes):
                    plt.plot(x, accuracy[mode][split], label=mode_names[idx],
                             color=colors[idx])
                plt.xlabel("Epoch")
                plt.ylabel("Accuracy")
                plt.title(f'All Modes - {split.capitalize()} Accuracy')
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(plot_dir, f"accuracy_all_modes_{split}.png"))
                plt.close()

        else:
            for idx, mode in enumerate(modes):
                mode_tag = mode_names[idx].lower().replace(" ", "_")
                plt.figure()
                plt.plot(x, accuracy[mode], label=mode_names[idx], color=colors[idx])
                plt.xlabel("Epoch")
                plt.ylabel("Accuracy")
                plt.title(f'{mode_names[idx]} Accuracy Over Epochs')
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(plot_dir, f"accuracy_{mode_tag}.png"))
                plt.close()

            # ✅ Combined plot of all modes
            plt.figure()
            for idx, mode in enumerate(modes):
                plt.plot(x, accuracy[mode], label=mode_names[idx],
                         color=colors[idx])
            plt.xlabel("Epoch")
            plt.ylabel("Accuracy")
            plt.title('Accuracy Over Epochs - All Modes')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(plot_dir, "accuracy_all_modes.png"))
            plt.close()

    else:
        raise ValueError("Invalid choice for plotting metrics. Use 'loss' or 'accuracy'.")

def plot_summary(summary, choice, metric_type="average"):
    assert metric_type in {"average", "final"}, "metric_type must be 'average' or 'final'"
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    plot_dir = "plots"
    os.makedirs(plot_dir, exist_ok=True)
    x = []
    prefix = metric_type  # e.g., "average" or "final"

    if choice == "loss":
        loss = []
        reg_loss = []
        nll_loss = []

        for round_num, data in summary.items():
            x.append(round_num)
            loss_data = data[metric_type]['loss']
            loss.append(loss_data.get('loss'))
            reg_loss.append(loss_data.get('reg_loss'))
            nll_loss.append(loss_data.get('nll_loss'))

        # All losses together
        plt.figure()
        plt.plot(x, loss, label='Total Loss')
        plt.plot(x, reg_loss, label='Regularization Loss')
        plt.plot(x, nll_loss, label='NLL Loss')
        plt.xlabel("Round")
        plt.ylabel("Loss Value")
        plt.title(f"{metric_type.capitalize()} Loss Metrics Per Round")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, f"{prefix}_loss_all_metrics.png"))
        plt.close()

        loss_components = [
            ('Total Loss', loss, 'loss_total.png'),
            ('Regularization Loss', reg_loss, 'loss_regularization.png'),
            ('NLL Loss', nll_loss, 'loss_nll.png'),
        ]

        # --- Plot each loss separately ---
        for i, (title, values, filename) in enumerate(loss_components):
            plt.figure()
            plt.plot(x, values, label=title, color=colors[i])
            plt.xlabel("Epoch")
            plt.ylabel("Loss Value")
            plt.title(f"{title} Over Epochs ({metric_type})")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(plot_dir, f"{prefix}_{filename}"))
            plt.close()

    elif choice == "accuracy":
        modes = [('mle', 'None'), ('flow', 'True'), ('flow', 'False')]
        eval_mode = 'train' in summary[0]['final'][modes[0]]['accuracy']
        mode_names = ['MLE Mode', 'Flow Mode with edit', 'Flow Mode without edit']
        accuracy = defaultdict(lambda: defaultdict(list)) if eval_mode else defaultdict(list)

        for round_num, data in summary.items():
            x.append(round_num)
            for mode in modes:
                mode_data = data[metric_type][mode]['accuracy'] if metric_type == "final" else data[metric_type][mode]
                if eval_mode:
                    for split in ['train', 'validation', 'test']:
                        accuracy[mode][split].append(mode_data[split])
                else:
                    accuracy[mode].append(mode_data['all'])
        if eval_mode:
            for idx, mode in enumerate(modes):
                mode_label = mode_names[idx]
                mode_tag = mode_label.lower().replace(" ", "_")
                # Each split individually
                for split_idx, split in enumerate(['train', 'validation', 'test']):
                    plt.figure()
                    plt.plot(x, accuracy[mode][split], label=f'{split.capitalize()} Accuracy',
                             color=colors[split_idx])
                    plt.xlabel("Round")
                    plt.ylabel("Accuracy")
                    plt.title(f'{mode_label} - {split.capitalize()} Accuracy ({metric_type})')
                    plt.grid(True)
                    plt.legend()
                    plt.tight_layout()
                    plt.savefig(os.path.join(plot_dir, f"{prefix}_accuracy_{mode_tag}_{split}.png"))
                    plt.close()

                # Combined split per mode
                plt.figure()
                for split_idx, split in enumerate(['train', 'validation', 'test']):
                    plt.plot(x, accuracy[mode][split], label=f'{split.capitalize()} Accuracy',
                             color=colors[split_idx])
                plt.xlabel("Round")
                plt.ylabel("Accuracy")
                plt.title(f'{mode_label} - All Splits ({metric_type})')
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(plot_dir, f"{prefix}_accuracy_{mode_tag}_all_splits.png"))
                plt.close()

            # Combined mode plot per split
            for split_idx, split in enumerate(['train', 'validation', 'test']):
                plt.figure()
                for idx, mode in enumerate(modes):
                    plt.plot(x, accuracy[mode][split], label=mode_names[idx],
                             color=colors[idx])
                plt.xlabel("Round")
                plt.ylabel("Accuracy")
                plt.title(f'All Modes - {split.capitalize()} Accuracy ({metric_type})')
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(plot_dir, f"{prefix}_accuracy_all_modes_{split}.png"))
                plt.close()
        else:
            # Handle the case where eval_mode is False
            for idx, mode in enumerate(modes):
                mode_label = mode_names[idx]
                mode_tag = mode_label.lower().replace(" ", "_")
                plt.figure()
                plt.plot(x, accuracy[mode], label=mode_label, color=colors[idx])
                plt.xlabel("Round")
                plt.ylabel("Accuracy")
                plt.title(f'{mode_label} ({metric_type})')
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(plot_dir, f"{prefix}_accuracy_{mode_tag}.png"))
                plt.close()
            # Combined plot of all modes
            plt.figure()
            for idx, mode in enumerate(modes):
                plt.plot(x, accuracy[mode], label=mode_names[idx],
                         color=colors[idx])
            plt.xlabel("Round")
            plt.ylabel("Accuracy")
            plt.title(f'All Modes ({metric_type})')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(plot_dir, f"{prefix}_accuracy_all_modes.png"))
            plt.close()
    else:
        raise ValueError("Invalid choice. Use 'loss' or 'accuracy'.")

plot_summary(summary, choice="loss", metric_type="average")
plot_summary(summary, choice="accuracy", metric_type="average")
plot_summary(summary, choice="loss", metric_type="final")
plot_summary(summary, choice="accuracy", metric_type="final")
plot_metrics(metrics, choice="loss")
plot_metrics(metrics, choice="accuracy")
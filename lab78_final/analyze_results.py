#!/usr/bin/env python3
import os
import csv
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from datetime import datetime
import numpy as np

def load_repository_results(repo_name, results_dir):
    csv_file = os.path.join(results_dir, repo_name, "results.csv")
    if not os.path.exists(csv_file):
        print(f"Results file not found for {repo_name}: {csv_file}")
        return None

    df = pd.read_csv(csv_file)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df["unique_cwes"] = df["unique_cwes"].apply(
        lambda x: [] if pd.isna(x) else x.split(",") if x else []
    )
    # Verifying if we have meaningful data to analyze:
    if df.empty:
        print(f"No data found for {repo_name}. Skipping analysis.")
        return None
        
    # Verifying we have some non-zero CWEs to analyze:
    cwe_count = df["unique_cwes"].apply(len).sum()
    if cwe_count == 0:
        print(f"Warning: No CWEs found in {repo_name}. Results may be incomplete.")
    
    return df   

def plot_individual_repository_metrics(repo_name, df, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Plot for confidence levels over time:
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["high_confidence"], "r-", label="High Confidence")
    plt.plot(df["date"], df["medium_confidence"], "y-", label="Medium Confidence")
    plt.plot(df["date"], df["low_confidence"], "g-", label="Low Confidence")
    plt.title(f"{repo_name}: Confidence Levels Over Time")
    plt.xlabel("Commit Date")
    plt.ylabel("Number of Issues")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{repo_name}_confidence.png"))
    plt.close()

    # Plot for severity levels over time:
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["high_severity"], "r-", label="High Severity")
    plt.plot(df["date"], df["medium_severity"], "y-", label="Medium Severity")
    plt.plot(df["date"], df["low_severity"], "g-", label="Low Severity")
    plt.title(f"{repo_name}: Severity Levels Over Time")
    plt.xlabel("Commit Date")
    plt.ylabel("Number of Issues")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{repo_name}_severity.png"))
    plt.close()

    # Get unique CWEs:
    all_cwes = []
    for cwes in df["unique_cwes"]:
        all_cwes.extend(cwes)

    # Plot of CWE frequency:
    cwe_counts = Counter(all_cwes)
    if all_cwes:
        top_cwes = dict(cwe_counts.most_common(10))

        plt.figure(figsize=(12, 6))
        plt.bar(top_cwes.keys(), top_cwes.values())
        plt.title(f"{repo_name}: Top 10 CWEs")
        plt.xlabel("CWE ID")
        plt.ylabel("Frequency")
        plt.grid(axis="y")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{repo_name}_cwes.png"))
        plt.close()

    return {
        "repo_name": repo_name,
        "total_commits": len(df),
        "avg_high_confidence": df["high_confidence"].mean(),
        "avg_medium_confidence": df["medium_confidence"].mean(),
        "avg_low_confidence": df["low_confidence"].mean(),
        "avg_high_severity": df["high_severity"].mean(),
        "avg_medium_severity": df["medium_severity"].mean(),
        "avg_low_severity": df["low_severity"].mean(),
        "unique_cwes_count": len(set(all_cwes)),
        "top_cwes": dict(cwe_counts.most_common(5)) if all_cwes else {},
    }


def answer_rq1(repositories_data, output_dir):
    """
    Answer RQ1: When are vulnerabilities with high severity introduced and fixed
    along the development timeline in OSS repositories?
    """
    print("Answering RQ1: High severity vulnerabilities introduction and fixing")

    # I define what it means for a vulnerability to be "fixed":
    # I'll consider a vulnerability fixed when the count decreases from one commit to the next
    for repo_name, df in repositories_data.items():
        # Calculating the changes in high severity issues between commits:
        df["high_severity_change"] = df["high_severity"].diff()
        df["high_severity_introduced"] = df["high_severity_change"].apply(
            lambda x: max(0, x)
        )
        df["high_severity_fixed"] = df["high_severity_change"].apply(
            lambda x: max(0, -x)
        )

    # Creating a comparative plot for all repositories:
    plt.figure(figsize=(15, 10))

    # Plot for high severity introductions:
    plt.subplot(2, 1, 1)
    for repo_name, df in repositories_data.items():
        # Normalization to percentage of commits that introduced vulnerabilities:
        introduced_pct = (df["high_severity_introduced"] > 0).mean() * 100
        fixed_pct = (df["high_severity_fixed"] > 0).mean() * 100

        plt.bar(
            [repo_name], [introduced_pct], alpha=0.7, label=f"{repo_name} (Introduced)"
        )
        plt.bar([f"{repo_name} (Fixed)"], [fixed_pct], alpha=0.7, color="green")

    plt.title(
        "Percentage of Commits that Introduce or Fix High Severity Vulnerabilities"
    )
    plt.ylabel("Percentage of Commits")
    plt.grid(axis="y")

    # Plot of the timeline of high severity issues:
    plt.subplot(2, 1, 2)
    for repo_name, df in repositories_data.items():
        plt.plot(
            range(len(df)),
            df["high_severity"].rolling(window=5).mean(),
            label=f"{repo_name} (5-commit rolling avg)",
        )

    plt.title("Timeline of High Severity Issues (Rolling Average)")
    plt.xlabel("Commit Sequence")
    plt.ylabel("Number of High Severity Issues")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "rq1_high_severity_analysis.png"))
    plt.close()
    
    summary = {"repo_stats": {}}
    for repo_name, df in repositories_data.items():
        introduced_commits = df[df["high_severity_introduced"] > 0]
        fixed_commits = df[df["high_severity_fixed"] > 0]

        summary["repo_stats"][repo_name] = {
            "total_commits": len(df),
            "commits_introducing_vulnerabilities": len(introduced_commits),
            "commits_fixing_vulnerabilities": len(fixed_commits),
            "percent_introducing": (
                len(introduced_commits) / len(df) * 100 if len(df) > 0 else 0
            ),
            "percent_fixing": len(fixed_commits) / len(df) * 100 if len(df) > 0 else 0,
            "avg_vulnerabilities_introduced_per_commit": (
                introduced_commits["high_severity_introduced"].mean()
                if len(introduced_commits) > 0
                else 0
            ),
            "avg_vulnerabilities_fixed_per_commit": (
                fixed_commits["high_severity_fixed"].mean()
                if len(fixed_commits) > 0
                else 0
            ),
        }

    # Calculating overall averages:
    all_introduced_pct = [
        stats["percent_introducing"] for stats in summary["repo_stats"].values()
    ]
    all_fixed_pct = [
        stats["percent_fixing"] for stats in summary["repo_stats"].values()
    ]

    summary["overall"] = {
        "avg_percent_introducing": (
            sum(all_introduced_pct) / len(all_introduced_pct)
            if all_introduced_pct
            else 0
        ),
        "avg_percent_fixing": (
            sum(all_fixed_pct) / len(all_fixed_pct) if all_fixed_pct else 0
        ),
        "ratio_fix_to_introduce": (
            sum(all_fixed_pct) / sum(all_introduced_pct)
            if sum(all_introduced_pct) > 0
            else 0
        ),
    }

    # Saving summary:
    with open(os.path.join(output_dir, "rq1_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def answer_rq2(repositories_data, output_dir):
    """
    Answer RQ2: Do vulnerabilities of different severity have the same pattern
    of introduction and elimination?
    """
    print(
        "Answering RQ2: Patterns of introduction and elimination across severity levels"
    )

    # Calculating changes for each severity level across all repositories:
    for repo_name, df in repositories_data.items():
        # High severity
        df["high_severity_change"] = df["high_severity"].diff()
        df["high_severity_introduced"] = df["high_severity_change"].apply(
            lambda x: max(0, x)
        )
        df["high_severity_fixed"] = df["high_severity_change"].apply(
            lambda x: max(0, -x)
        )

        # Medium severity
        df["medium_severity_change"] = df["medium_severity"].diff()
        df["medium_severity_introduced"] = df["medium_severity_change"].apply(
            lambda x: max(0, x)
        )
        df["medium_severity_fixed"] = df["medium_severity_change"].apply(
            lambda x: max(0, -x)
        )

        # Low severity
        df["low_severity_change"] = df["low_severity"].diff()
        df["low_severity_introduced"] = df["low_severity_change"].apply(
            lambda x: max(0, x)
        )
        df["low_severity_fixed"] = df["low_severity_change"].apply(lambda x: max(0, -x))

    plt.figure(figsize=(15, 12))
    
    # Plot 1: Introduction rates
    plt.subplot(2, 1, 1)
    labels = []
    high_intro_rates = []
    medium_intro_rates = []
    low_intro_rates = []
    for repo_name, df in repositories_data.items():
        labels.append(repo_name)
        high_intro_rates.append((df["high_severity_introduced"] > 0).mean() * 100)
        medium_intro_rates.append((df["medium_severity_introduced"] > 0).mean() * 100)
        low_intro_rates.append((df["low_severity_introduced"] > 0).mean() * 100)
    x = np.arange(len(labels))
    width = 0.25
    plt.bar(
        x - width,
        high_intro_rates,
        width,
        label="High Severity",
        color="red",
        alpha=0.7,
    )
    plt.bar(
        x, medium_intro_rates, width, label="Medium Severity", color="orange", alpha=0.7
    )
    plt.bar(
        x + width,
        low_intro_rates,
        width,
        label="Low Severity",
        color="green",
        alpha=0.7,
    )
    plt.ylabel("Percentage of Commits Introducing Vulnerabilities")
    plt.title("Introduction Rate by Severity Level")
    plt.xticks(x, labels, rotation=45)
    plt.legend()
    plt.grid(axis="y")

    # Plot 2: Fix rates
    plt.subplot(2, 1, 2)
    high_fix_rates = []
    medium_fix_rates = []
    low_fix_rates = []
    for repo_name, df in repositories_data.items():
        high_fix_rates.append((df["high_severity_fixed"] > 0).mean() * 100)
        medium_fix_rates.append((df["medium_severity_fixed"] > 0).mean() * 100)
        low_fix_rates.append((df["low_severity_fixed"] > 0).mean() * 100)
    plt.bar(
        x - width, high_fix_rates, width, label="High Severity", color="red", alpha=0.7
    )
    plt.bar(
        x, medium_fix_rates, width, label="Medium Severity", color="orange", alpha=0.7
    )
    plt.bar(
        x + width, low_fix_rates, width, label="Low Severity", color="green", alpha=0.7
    )
    plt.ylabel("Percentage of Commits Fixing Vulnerabilities")
    plt.title("Fix Rate by Severity Level")
    plt.xticks(x, labels, rotation=45)
    plt.legend()
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "rq2_severity_patterns.png"))
    plt.close()

    # Create a ratio plot (fix rate / introduction rate)
    plt.figure(figsize=(12, 8))

    high_ratios = [
        fix / intro if intro > 0 else 0
        for fix, intro in zip(high_fix_rates, high_intro_rates)
    ]
    medium_ratios = [
        fix / intro if intro > 0 else 0
        for fix, intro in zip(medium_fix_rates, medium_intro_rates)
    ]
    low_ratios = [
        fix / intro if intro > 0 else 0
        for fix, intro in zip(low_fix_rates, low_intro_rates)
    ]

    plt.bar(
        x - width, high_ratios, width, label="High Severity", color="red", alpha=0.7
    )
    plt.bar(x, medium_ratios, width, label="Medium Severity", color="orange", alpha=0.7)
    plt.bar(
        x + width, low_ratios, width, label="Low Severity", color="green", alpha=0.7
    )

    plt.axhline(y=1.0, color="black", linestyle="--")
    plt.text(x[-1] + width + 0.5, 1.0, "Balance point", verticalalignment="center")
    plt.ylabel("Fix Rate / Introduction Rate")
    plt.title("Ratio of Fix Rate to Introduction Rate by Severity Level")
    plt.xticks(x, labels, rotation=45)
    plt.legend()
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "rq2_fix_intro_ratio.png"))
    plt.close()

    summary = {"repo_stats": {}, "severity_comparisons": {}}
    for repo_name, df in repositories_data.items():
        summary["repo_stats"][repo_name] = {
            "high_severity": {
                "intro_rate": (df["high_severity_introduced"] > 0).mean() * 100,
                "fix_rate": (df["high_severity_fixed"] > 0).mean() * 100,
                "ratio": (
                    (df["high_severity_fixed"] > 0).mean()
                    / (df["high_severity_introduced"] > 0).mean()
                    if (df["high_severity_introduced"] > 0).mean() > 0
                    else 0
                ),
            },
            "medium_severity": {
                "intro_rate": (df["medium_severity_introduced"] > 0).mean() * 100,
                "fix_rate": (df["medium_severity_fixed"] > 0).mean() * 100,
                "ratio": (
                    (df["medium_severity_fixed"] > 0).mean()
                    / (df["medium_severity_introduced"] > 0).mean()
                    if (df["medium_severity_introduced"] > 0).mean() > 0
                    else 0
                ),
            },
            "low_severity": {
                "intro_rate": (df["low_severity_introduced"] > 0).mean() * 100,
                "fix_rate": (df["low_severity_fixed"] > 0).mean() * 100,
                "ratio": (
                    (df["low_severity_fixed"] > 0).mean()
                    / (df["low_severity_introduced"] > 0).mean()
                    if (df["low_severity_introduced"] > 0).mean() > 0
                    else 0
                ),
            },
        }

    # Calculating overall averages:
    high_intro_avg = (
        sum(high_intro_rates) / len(high_intro_rates) if high_intro_rates else 0
    )
    medium_intro_avg = (
        sum(medium_intro_rates) / len(medium_intro_rates) if medium_intro_rates else 0
    )
    low_intro_avg = (
        sum(low_intro_rates) / len(low_intro_rates) if low_intro_rates else 0
    )

    high_fix_avg = sum(high_fix_rates) / len(high_fix_rates) if high_fix_rates else 0
    medium_fix_avg = (
        sum(medium_fix_rates) / len(medium_fix_rates) if medium_fix_rates else 0
    )
    low_fix_avg = sum(low_fix_rates) / len(low_fix_rates) if low_fix_rates else 0

    summary["severity_comparisons"] = {
        "introduction_rates": {
            "high_severity_avg": high_intro_avg,
            "medium_severity_avg": medium_intro_avg,
            "low_severity_avg": low_intro_avg,
        },
        "fix_rates": {
            "high_severity_avg": high_fix_avg,
            "medium_severity_avg": medium_fix_avg,
            "low_severity_avg": low_fix_avg,
        },
        "fix_to_intro_ratios": {
            "high_severity_avg": (
                high_fix_avg / high_intro_avg if high_intro_avg > 0 else 0
            ),
            "medium_severity_avg": (
                medium_fix_avg / medium_intro_avg if medium_intro_avg > 0 else 0
            ),
            "low_severity_avg": low_fix_avg / low_intro_avg if low_intro_avg > 0 else 0,
        },
    }

    # Saving summary:
    with open(os.path.join(output_dir, "rq2_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def answer_rq3(repositories_data, output_dir):
    """
    Answer RQ3: Which CWEs are the most frequent across different OSS repositories?
    """
    print("Answering RQ3: Most frequent CWEs across repositories")

    # Collecting all CWEs from all repositories:
    all_cwes = []
    repo_cwes = {}

    for repo_name, df in repositories_data.items():
        repo_cwes[repo_name] = []
        for cwes in df["unique_cwes"]:
            repo_cwes[repo_name].extend(cwes)
            all_cwes.extend(cwes)

    # Counting the overall CWE frequencies:
    cwe_counts = Counter(all_cwes)
    if not all_cwes:
        print("WARNING: No CWEs found in any repository. Cannot answer RQ3.")

        plt.figure(figsize=(10, 6))
        plt.text(
            0.5,
            0.5,
            "No CWEs found in any repository",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=16,
        )
        plt.axis("off")
        plt.savefig(os.path.join(output_dir, "rq3_no_cwes.png"))
        plt.close()
        return {
            "overall_top_cwes": {},
            "repository_top_cwes": {
                repo_name: {} for repo_name in repositories_data.keys()
            },
        }

    top_cwes = cwe_counts.most_common(min(10, len(cwe_counts)))
    plt.figure(figsize=(12, 8))
    labels = [f"CWE-{cwe}" for cwe, _ in top_cwes]
    values = [count for _, count in top_cwes]
    plt.bar(labels, values)
    plt.title("Most Frequent CWEs Across All Repositories")
    plt.xlabel("CWE ID")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "rq3_top_cwes.png"))
    plt.close()

    # Create a heatmap showing CWE distribution across repositories, but only if we have data
    if (
        top_cwes and len(repo_cwes) > 1
    ):  # Only create heatmap if we have multiple repos and CWEs
        top_cwe_ids = [cwe for cwe, _ in top_cwes]
        repo_cwe_matrix = []
        repo_names = []

        for repo_name, cwes in repo_cwes.items():
            # Skip repos with no CWEs
            if not cwes:
                continue
            repo_names.append(repo_name)

            # Count CWEs for this repository
            repo_counter = Counter(cwes)

            # Create a row for the matrix
            row = [repo_counter.get(cwe, 0) for cwe in top_cwe_ids]
            repo_cwe_matrix.append(row)

        # Only create heatmap if we have data
        if repo_names and repo_cwe_matrix and len(repo_cwe_matrix[0]) > 0:
            plt.figure(figsize=(14, 8))
            sns.heatmap(
                repo_cwe_matrix,
                annot=True,
                fmt="d",
                xticklabels=[f"CWE-{cwe}" for cwe in top_cwe_ids],
                yticklabels=repo_names,
                cmap="YlOrRd",
            )
            plt.title("Distribution of Top CWEs Across Repositories")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "rq3_cwe_heatmap.png"))
            plt.close()

    # Preparing summary:
    summary = {
        "overall_top_cwes": {f"CWE-{cwe}": count for cwe, count in top_cwes},
        "repository_top_cwes": {},
    }
    for repo_name, cwes in repo_cwes.items():
        if cwes:
            repo_counter = Counter(cwes)
            summary["repository_top_cwes"][repo_name] = {
                f"CWE-{cwe}": count for cwe, count in repo_counter.most_common(5)
            }
        else:
            summary["repository_top_cwes"][repo_name] = {}

    # Saving summary:
    with open(os.path.join(output_dir, "rq3_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main():
    base_dir = "bandit_analysis_results"
    output_dir = os.path.join(base_dir, "analysis_outputs")
    os.makedirs(output_dir, exist_ok=True)
    repositories = ["bandit", "manim", "flask"]
    repositories_data = {}
    repositories_summaries = {}

    for repo_name in repositories:
        print(f"Loading data for {repo_name}...")
        df = load_repository_results(repo_name, base_dir)
        if df is not None:
            repositories_data[repo_name] = df
            repo_output_dir = os.path.join(output_dir, repo_name)
            os.makedirs(repo_output_dir, exist_ok=True)
            print(f"Creating plots for {repo_name}...")
            repo_summary = plot_individual_repository_metrics(
                repo_name, df, repo_output_dir
            )
            repositories_summaries[repo_name] = repo_summary
        else:
            print(f"WARNING: Could not load data for {repo_name}")

    if not repositories_data:
        print(
            "ERROR: No repository data could be loaded. Check that the CSV files exist."
        )
        return

    print("Answering research questions...")
    rq1_summary = answer_rq1(repositories_data, output_dir)
    rq2_summary = answer_rq2(repositories_data, output_dir)
    rq3_summary = answer_rq3(repositories_data, output_dir)

    report = {
        "repositories": repositories_summaries,
        "research_questions": {
            "rq1": rq1_summary,
            "rq2": rq2_summary,
            "rq3": rq3_summary,
        },
    }

    with open(os.path.join(output_dir, "consolidated_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print("Analysis complete! Results saved to:", output_dir)


if __name__ == "__main__":
    main()

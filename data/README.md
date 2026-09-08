# VRPTW data

This directory contains the **Solomon Vehicle Routing Problem with Time Windows (VRPTW)** benchmark instances used as toy data for this project.

The data is based on the benchmark introduced by:

> Solomon, M. M. (1987). *Algorithms for the Vehicle Routing and Scheduling Problems with Time Window Constraints*. Operations Research, 35(2), 254–265.

The original benchmark is widely used to evaluate algorithms for the Vehicle Routing Problem with Time Windows (VRPTW).

The dataset used in this project was obtained from the
[Solomon VRPTW Benchmark on Kaggle](https://www.kaggle.com/datasets/masud7866/solomon-vrptw-benchmark).

---

## 1. Problem Overview

The **Vehicle Routing Problem with Time Windows (VRPTW)** consists of a fleet of vehicles that must serve a set of customers while respecting:

- vehicle capacity;
- customer demand;
- customer time windows;
- service duration;
- vehicle availability;
- depot constraints.

Every vehicle starts and finishes at the **depot**.

The optimization problem is typically concerned with finding a set of routes that serves every customer while minimizing a routing cost, commonly:

1. the number of vehicles used; and
2. the total travel distance.

The Solomon benchmark provides standardized instances for comparing different optimization approaches.

---

## 2. Dataset Structure

The Solomon benchmark is divided into six instance families:

| Family | Customer distribution | Scheduling horizon |
|---|---|---|
| `C1` | Clustered | Short |
| `C2` | Clustered | Long |
| `R1` | Random | Short |
| `R2` | Random | Long |
| `RC1` | Random + Clustered | Short |
| `RC2` | Random + Clustered | Long |

The first letter describes the spatial distribution of customers:

- **C** — customers are geographically clustered.
- **R** — customers are randomly distributed.
- **RC** — customers contain both random and clustered characteristics.

The second digit describes the scheduling horizon:

- **1** — short scheduling horizon.
- **2** — long scheduling horizon.

This distinction affects the number of customers that can typically be served by a single vehicle. Short-horizon instances generally result in fewer customers per route, while long-horizon instances allow substantially more customers per route. :contentReference[oaicite:1]{index=1}

Examples:

```text
C101   -> clustered customers, short horizon
C201   -> clustered customers, long horizon

R101   -> randomly distributed customers, short horizon
R201   -> randomly distributed customers, long horizon

RC101  -> mixed distribution, short horizon
RC201  -> mixed distribution, long horizon
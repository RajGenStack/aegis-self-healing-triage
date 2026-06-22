# Smart Patient Triage System with Self-Healing Infrastructure

A real-time healthcare monitoring system built on AWS that tracks patient vitals, calculates clinical risk scores, and features self-healing infrastructure to survive outages automatically.

## Project Roadmap

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | **Vitals Simulator + Scoring Logic (Python)** | **Completed** |
| **Phase 2** | **Core AWS Pipeline (SQS → Lambda → DynamoDB via Terraform)** | **Completed** |
| **Phase 3** | **React Triage Dashboard (NEWS2 Clinical Urgency)** | **Completed** |
| **Phase 4** | **CI/CD Pipeline (GitHub Actions automatic deployments)** | **Completed** |
| **Phase 5** | Observability (CloudWatch dashboards & alarms) | Planned |
| **Phase 6** | Chaos Engineering (Custom outage injection script) | Planned |
| **Phase 7** | Self-Healing (Automated EventBridge remediation loop) | Planned |
| **Phase 8** | Postmortem & Documentation (MTTR reports + architecture) | Planned |

---

## Phase 1: Vitals Simulator & NEWS2 Scoring Logic

Phase 1 establishes the patient simulation and clinical triage scoring engine locally. The engine computes risk using the clinical **National Early Warning Score 2 (NEWS2)** standard.

### NEWS2 Scoring Matrix

The NEWS2 score assigns weighting (0–3 points) based on deviation from normal physiological ranges.

| Parameter | 3 Points | 2 Points | 1 Point | 0 Points | 1 Point | 2 Points | 3 Points |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Respiration Rate** | ≤ 8 | - | 9–11 | 12–20 | - | 21–24 | ≥ 25 |
| **SpO₂ Scale 1** (Standard) | ≤ 91 | 92–93 | 94–95 | ≥ 96 | - | - | - |
| **SpO₂ Scale 2** (COPD) | ≤ 83 | 84–85 | 86–87 | 88–92 | 93–94 (O₂) | 95–96 (O₂) | ≥ 97 (O₂) |
| **Supplemental Oxygen** | - | Yes | - | No (Air) | - | - | - |
| **Systolic BP** | ≤ 90 | 91–100 | 101–110 | 111–219 | - | - | ≥ 220 |
| **Heart Rate** | ≤ 40 | - | 41–50 | 51–90 | 91–110 | 111–130 | ≥ 131 |
| **Temperature (°C)** | ≤ 35.0 | - | 35.1–36.0 | 36.1–38.0 | 38.1–39.0 | ≥ 39.1 | - |
| **Consciousness (CVPU)**| - | - | - | Alert | - | - | Confused/Voice/Pain/Unresponsive |

#### Triage Risk Level Calculation
- **LOW** (Green): Total score 0–4 AND no single parameter scores 3 points.
- **MEDIUM** (Amber): Total score 5–6 OR any single parameter scores 3 points (representing urgent clinical review trigger).
- **HIGH** (Red): Total score ≥ 7.

---

### Files

- `simulator/vitals_simulator.py`: Python script simulating patient profiles (`STABLE`, `RECOVERING`, `DETERIORATING`, `CRITICAL`) and computing NEWS2 scores.
- `simulator/triage_scoring.py`: Centralized scoring engine implementing standard clinical logic.
- `simulator/tests/test_triage_scoring.py`: Unit tests validating NEWS2 threshold boundaries.

---

### Getting Started

#### Run Unit Tests
To run the automated test suite locally:
```bash
python -m unittest discover -s simulator/tests
```

#### Run the Simulator CLI
To simulate vitals output as JSON lines streaming directly to standard output:
```bash
python simulator/vitals_simulator.py --patients 5 --interval 2 --duration 30
```

**Parameters:**
* `--patients`: Number of patients to simulate (default: 5)
* `--copd-ratio`: Ratio of patients configured with COPD SpO2 target range (default: 0.2)
* `--duration`: How long to run in seconds. Set to `0` to run indefinitely (default: 0)
* `--interval`: Time between vitals checks per patient in seconds (default: 2.0)
* `--output`: Output file path to write JSON logs to (optional)
* `--sqs-queue`: Target AWS SQS Queue name to stream JSON vitals data (optional)

#### Stream Vitals to AWS SQS (Phase 2 Ingestion)
To run the simulator and stream patient data directly to the SQS queue:
```bash
python simulator/vitals_simulator.py --patients 5 --interval 2 --duration 30 --sqs-queue rajgenstack-triage-vitals-queue
```
*Note: Ensure your AWS credentials are properly configured locally (`aws configure`) before running.*

---

## Phase 3: React Triage Dashboard

Phase 3 introduces a clean clinical light-mode patient health dashboard that polls AWS Lambda API Function URLs, displaying real-time patient states sorted by clinical score under Indian patient identities (e.g., Priya Singh, Aditi Patel).

### Launching the Dashboard Locally

1.  **Install dependencies**:
    ```bash
    cd frontend
    npm.cmd install
    ```
2.  **Start development server**:
    ```bash
    npm.cmd run dev
    ```
3.  **Open browser**: Navigate to `http://localhost:5173/` to view the live dashboard.

---

## Phase 4: CI/CD Pipeline (GitHub Actions)

Phase 4 introduces a GitHub Actions pipeline configured in `.github/workflows/ci-cd.yml` to validate incoming contributions automatically and deploy them to AWS on merging.

### Workflow Pipeline Jobs

1.  **Run Python Tests**: Sets up Python, installs dependencies, and runs all simulator unittest classes.
2.  **Validate Terraform**: Performs Terraform lint checks (`terraform fmt`) and code validation (`terraform validate`).
3.  **Build Frontend**: Installs Node packages and compiles the React production build (`npm run build`) to ensure bundler integrity.
4.  **AWS Deployment (CD)**: Automatically applies Terraform changes on merge to the `main` branch.

### Setting up AWS Secrets in GitHub

To enable automated CD deployment, add these repository secrets in GitHub under **Settings -> Secrets and Variables -> Actions**:
*   `AWS_ACCESS_KEY_ID`: Your AWS access key.
*   `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
*   `AWS_REGION`: The target AWS deployment region (e.g., `us-east-1`).



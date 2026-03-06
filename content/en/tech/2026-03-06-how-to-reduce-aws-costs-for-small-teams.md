---
title: "How to Reduce AWS Costs for Small Teams: A Practical Guide"
date: 2026-03-06T19:55:06+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "reduce", "aws", "costs", "Python"]
description: "Stop overpaying on AWS. Discover why bills spike $2,000+ between quarters and the exact steps small teams can take to reduce AWS costs fast."
image: "/images/20260306-how-to-reduce-aws-costs-for-sm.webp"
technologies: ["Python", "Docker", "AWS", "Go", "Slack"]
faq:
  - question: "how to reduce AWS costs for small teams without a dedicated FinOps person"
    answer: "Small teams can reduce AWS costs by focusing on three high-impact areas: right-sizing over-provisioned EC2 instances, scheduling non-production environments to shut down outside business hours, and activating free tools like AWS Cost Explorer and Compute Optimizer. According to Flexera's 2025 State of the Cloud report, small teams waste 30–40% of their AWS spend on idle or over-provisioned resources. These changes require no dedicated FinOps analyst and can be implemented with basic CLI access."
  - question: "what percentage of AWS spend do small teams waste on average"
    answer: "According to Flexera's 2025 State of the Cloud report, organizations waste an average of 32% of cloud spend, and the number skews higher for small teams who lack a dedicated person monitoring costs. The three biggest drivers are over-provisioned instances, idle dev environments running 24/7, and missing lifecycle policies on S3 buckets, EBS snapshots, and old AMIs. Addressing just the first two categories — compute right-sizing and non-production scheduling — delivers the highest ROI for teams under 20 engineers."
  - question: "AWS Savings Plans vs Reserved Instances which is better for small teams"
    answer: "Savings Plans are generally the better choice for small teams because they offer more flexibility than Reserved Instances when workloads change over time. A 1-year Savings Plan commitment can cut on-demand EC2 pricing by up to 66%, while still allowing you to shift usage across instance types, regions, and services. Reserved Instances lock you into a specific instance configuration, which creates risk if your team's infrastructure needs evolve."
  - question: "how to reduce AWS costs for small teams using Spot Instances"
    answer: "Spot Instances can cut compute costs by up to 90% compared to on-demand pricing, but they come with a high operational risk — AWS can reclaim them with two minutes' notice. They work best for fault-tolerant workloads like batch processing, data pipelines, and CI/CD jobs, where an interruption doesn't break production. Small teams should avoid Spot Instances for production APIs or stateful workloads where an unexpected shutdown would cause an outage."
  - question: "does AWS Cost Explorer cost money to use"
    answer: "AWS Cost Explorer and Compute Optimizer are both free to activate and use for standard cost analysis and rightsizing recommendations. Compute Optimizer surfaces actionable EC2 rightsizing recommendations within approximately 14 days of activation, based on your actual usage patterns. The tools are built into the AWS console but are not enabled by default, so small teams need to manually activate them to start seeing recommendations."
---

AWS bills have a way of quietly doubling between January and March. One month you're humming along, the next you're staring at an invoice that's somehow $2,000 higher than last quarter — and you have no idea which service ate the difference.

This guide is for developers and engineers running real workloads — staging environments, production APIs, background jobs — on teams too small for a dedicated FinOps analyst. By the end, you'll know exactly where small teams overspend, which tools surface the waste, and how to cut your bill without touching performance.

**What you'll learn:**
- Which AWS services drain small-team budgets fastest
- How to right-size EC2 instances with real CLI commands
- How to automate cost guardrails so you don't have to babysit dashboards
- Where Spot Instances and Savings Plans make sense — and where they don't

---

> **Key Takeaways**
> - Small teams waste 30–40% of their AWS spend on idle or over-provisioned resources, per Flexera's 2025 State of the Cloud report.
> - EC2 right-sizing and scheduling non-production environment shutdowns deliver the highest ROI for teams under 20 engineers.
> - AWS Cost Explorer and Compute Optimizer are free and surface actionable recommendations within 14 days of activation.
> - Savings Plans cut on-demand pricing by up to 66% with a 1-year commitment — and they're more flexible than Reserved Instances for teams with changing workloads.
> - Tagging every resource at launch — not retroactively — is the single habit that makes every other cost-cutting effort actually work.

---

## Background & Context

AWS launched its cost management toolset incrementally over the past decade — Cost Explorer in 2014, Compute Optimizer in 2019, and Cost Anomaly Detection in 2020. These tools are genuinely useful. They're also buried deep in the console, and most small teams never activate them.

The 2025 Flexera State of the Cloud report found that organizations waste an average of 32% of cloud spend. For small teams, that number skews higher — there's no dedicated person watching the dashboard.

Three things drive most of the waste:
1. **Over-provisioned instances** — launched at peak capacity estimates, never right-sized
2. **Idle resources** — dev environments running 24/7 when they're actually used 8 hours a day
3. **Missing lifecycle policies** — S3 buckets, EBS snapshots, and old AMIs accumulating silently

The prerequisite knowledge here is basic: you should know what EC2, S3, and IAM are. CLI access with appropriate permissions is assumed.

---

## Comparison: AWS Cost Reduction Approaches

| Strategy | Effort | Savings Potential | Risk Level | Best For |
|---|---|---|---|---|
| Right-sizing EC2 instances | Medium | 20–40% on compute | Low | Teams with stable workloads |
| Savings Plans (1-year) | Low | Up to 66% on compute | Low-Medium | Predictable baseline usage |
| Spot Instances | High | Up to 90% on compute | High | Batch jobs, fault-tolerant workloads |
| Scheduled start/stop (non-prod) | Low | 60–70% on idle envs | Very Low | Dev/staging environments |
| S3 lifecycle policies | Low | 30–50% on storage | Very Low | Teams with large object storage |

Right-sizing delivers consistent returns without operational complexity — start there. Savings Plans are the better version of Reserved Instances for small teams because they apply across instance families and regions. Spot Instances can save serious money on CI/CD pipelines and data processing jobs, but you need to architect for interruption.

The scheduled start/stop approach is underrated. A staging environment that runs 10 hours a day instead of 24 saves roughly 58% of its compute cost with zero architectural change. No refactoring, no migration — just a cron job and a tag.

---

## Step-by-Step Implementation Guide

### Prerequisites
- AWS CLI v2 installed and configured (`aws --version`)
- IAM permissions: `ce:*`, `compute-optimizer:*`, `ec2:Describe*`, `ec2:StopInstances`
- Cost Explorer enabled (free, takes up to 24 hours to activate)
- Basic familiarity with AWS console or CLI

---

### Step 1: Activate AWS Compute Optimizer and Pull Recommendations

Compute Optimizer uses CloudWatch metrics to analyze your EC2 instances over 14 days and recommends cheaper alternatives.

```bash
# Enable Compute Optimizer for your account
aws compute-optimizer update-enrollment-status \
  --status Active \
  --region us-east-1

# After 14 days, pull EC2 recommendations to a CSV
aws compute-optimizer get-ec2-instance-recommendations \
  --output json \
  --query 'instanceRecommendations[].{
    Instance:instanceArn,
    CurrentType:currentInstanceType,
    RecommendedType:recommendationOptions[0].instanceType,
    SavingsMonthly:recommendationOptions[0].estimatedMonthlySavings.value
  }' \
  | jq -r '.[] | [.Instance, .CurrentType, .RecommendedType, .SavingsMonthly] | @csv'
```

Expected output: a list of instances with their current type, recommended type, and estimated monthly savings. An `m5.xlarge` running at 8% CPU is a common find — Compute Optimizer will flag it for downsizing to `m5.large`. That one swap can save $30–50/month per instance before you've changed a single line of application code.

---

### Step 2: Schedule Non-Production Environments to Stop Overnight

This single script has saved teams hundreds of dollars per month. Tag your dev and staging instances with `Environment=dev`, then run this on a schedule via EventBridge.

```bash
# Stop all instances tagged Environment=dev
# Run this via AWS Lambda + EventBridge at 8 PM weekdays
aws ec2 stop-instances \
  --instance-ids $(aws ec2 describe-instances \
    --filters "Name=tag:Environment,Values=dev" \
               "Name=instance-state-name,Values=running" \
    --query "Reservations[].Instances[].InstanceId" \
    --output text) \
  --region us-east-1
```

Pair this with a matching `start-instances` call at 8 AM. A `t3.medium` dev instance at $0.0416/hour runs about $30/month at 24/7. Drop it to 10 hours/weekday and it costs roughly $8.50/month. That's a 72% reduction per instance — and if you have five dev instances, that's over $100/month recovered from a single script.

This approach can fail when developers leave long-running processes on instances they expect to be up in the morning. Set expectations with your team before flipping the switch, and build in a manual override path for edge cases.

---

### Step 3: Set S3 Lifecycle Policies to Move Old Objects to Glacier

Most teams store logs and backups in S3 Standard indefinitely. S3 Standard costs $0.023/GB. S3 Glacier Instant Retrieval costs $0.004/GB — an 83% drop.

```json
{
  "Rules": [
    {
      "ID": "MoveLogsToGlacier",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "logs/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER_IR"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

```bash
# Apply the lifecycle policy to your bucket
aws s3api put-bucket-lifecycle-configuration \
  --bucket your-logs-bucket-name \
  --lifecycle-configuration file://lifecycle-policy.json
```

After 90 days, logs automatically move to Glacier. After 365 days, they're deleted. Zero manual intervention after setup. One caveat: Glacier retrieval takes minutes, not milliseconds. Don't apply this to buckets where you need sub-second access to older objects.

---

### Step 4: Enable Cost Anomaly Detection Alerts

```bash
# Create a cost monitor for your entire AWS account
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "TeamCostMonitor",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

# Create an alert subscription — replace with your team email
aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "SlackAlerts",
    "MonitorArnList": ["PASTE_MONITOR_ARN_HERE"],
    "Subscribers": [
      {
        "Address": "your-team@company.com",
        "Type": "EMAIL"
      }
    ],
    "Threshold": 20,
    "Frequency": "DAILY"
  }'
```

This fires an alert when any service's spend increases by 20% above its normal baseline. It catches a runaway Lambda loop or a forgotten data transfer before it compounds into a four-figure surprise at month-end.

---

### Step 5: Purchase a Compute Savings Plan

Once you've right-sized and you have 14+ days of stable usage data, pull your Savings Plan recommendations.

```bash
# Pull Savings Plan purchase recommendations
aws savingsplans list-savings-plans-purchase-recommendation \
  --savings-plans-type COMPUTE_SP \
  --term-in-years ONE_YEAR \
  --payment-option NO_UPFRONT \
  --lookback-period-in-days THIRTY_DAYS
```

Compute Savings Plans apply across all EC2 instance families, regions, and sizes — and cover Lambda and Fargate too. For a team spending $1,000/month on compute, a 1-year no-upfront Compute Savings Plan typically drops that bill to $600–700/month. That's $3,600–4,800/year back in your budget, with no architectural changes required.

---

## Code Examples & Real-World Use Cases

### Basic Example: Tag All Untagged EC2 Instances

Untagged resources make cost allocation impossible. Run this monthly as a hygiene check.

```python
import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

def find_untagged_instances():
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}]
    )
    
    untagged = []
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            
            # Check for required cost allocation tags
            if 'Environment' not in tags or 'Team' not in tags:
                untagged.append({
                    'InstanceId': instance['InstanceId'],
                    'Type': instance['InstanceType'],
                    'MissingTags': [k for k in ['Environment', 'Team'] if k not in tags]
                })
    
    return untagged

if __name__ == '__main__':
    results = find_untagged_instances()
    for r in results:
        print(f"⚠️  {r['InstanceId']} ({r['Type']}) missing: {', '.join(r['MissingTags'])}")
```

**Use case:** Run this in CI/CD as a weekly audit. When a developer spins up an instance without tagging it, the script surfaces it before the next billing cycle closes.

### Advanced Example: Cost Report by Team Tag

```python
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce', region_name='us-east-1')

def get_cost_by_team(days_back=30):
    end = datetime.today().strftime('%Y-%m-%d')
    start = (datetime.today() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {'Type': 'TAG', 'Key': 'Team'}  # requires cost allocation tags enabled
        ]
    )
    
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            team = group['Keys'][0].replace('Team$', '') or 'Untagged'
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            print(f"{team}: ${cost:.2f}")

if __name__ == '__main__':
    get_cost_by_team()
```

**Use case:** Drop this into a Lambda on a monthly schedule and pipe the output to Slack. Each team sees exactly what their workloads cost — accountability without spreadsheets, without a FinOps hire.

---

## Best Practices & Tips

### Common Pitfalls to Avoid

- **Over-committing to Reserved Instances**: Small teams change instance types often. Savings Plans cover more scenarios and don't lock you into a specific instance family. Stick with Savings Plans unless you have 12+ months of identical usage patterns. Check your Compute Optimizer recommendations *before* making any commitment purchase.

- **Ignoring data transfer costs**: EC2 outbound data to the internet is $0.09/GB. For APIs returning large payloads, this compounds fast — and it won't show up in your compute costs line. Enable CloudFront in front of APIs serving large or cacheable responses. Data transfer from EC2 to CloudFront is free.

- **Retroactive tagging**: Adding tags after resources are created is painful and error-prone. Untagged resources mean unallocated costs — which means you can't prove to anyone where the money went. Use AWS Service Control Policies (SCPs) to require specific tags at resource creation, so the problem never starts.

### Optimization Tips

- Set a billing alert at 80% of your expected monthly budget via CloudWatch. It takes 3 minutes to configure and prevents the "how did we hit $4,000?" conversation.
- Restrict Cost Explorer and Billing Console access to specific IAM roles. Not every developer needs to see the full bill, but a designated cost owner absolutely should.
- Graviton3 (ARM-based) instances like `m7g` are 20–40% cheaper than equivalent `m7i` (x86) instances for most workloads. If your Docker images support multi-arch builds, switching instance families is a low-effort win with no application changes required.

### Production Readiness Checklist

- [ ] Compute Optimizer enabled and reviewed after 14 days
- [ ] All EC2 instances tagged with `Environment`, `Team`, and `Project`
- [ ] Non-production instances have a scheduled stop/start via EventBridge
- [ ] S3 lifecycle policies applied to log and backup buckets
- [ ] Cost Anomaly Detection active with email or Slack alerts
- [ ] Savings Plan coverage reviewed quarterly
- [ ] Data transfer costs reviewed monthly in Cost Explorer

---

## Conclusion & Next Steps

Cutting your AWS bill as a small team comes down to four repeatable actions: right-size your instances, stop what you're not using, archive what you're not accessing, and automate the monitoring so it doesn't require weekly attention.

None of this is clever. It's consistent.

Start with the highest-leverage moves first — the ones that require the least architectural change and pay off immediately:

1. Enable Compute Optimizer today — it's free and needs 14 days of data before it's useful
2. Apply the scheduled stop/start script to every dev and staging environment this week
3. Add S3 lifecycle policies to your three largest buckets
4. Set a billing anomaly alert at a 20% threshold

The full documentation lives at [aws.amazon.com/aws-cost-management](https://aws.amazon.com/aws-cost-management/). Flexera's annual State of the Cloud report is worth bookmarking — it tracks industry benchmarks you can compare against your own numbers to gauge whether your spend is reasonable or outlying.

Once these steps are in place, the logical next topic is container cost optimization — specifically whether Fargate Spot or EKS on Graviton fits your workload better than your current setup. That's where the next layer of savings tends to hide for teams that have already cleaned up the basics.

## References

1. [How to Reduce AWS Costs Without Sacrificing Performance?](https://www.cloudjournee.com/blog/how-to-reduce-aws-costs-without-sacrificing-performance/)
2. [22 Best AWS Cost Optimization Tools & 12+ Strategies for You | Sedai](https://sedai.io/blog/how-to-optimize-for-cost-in-ec2-aws)
3. [AWS cost optimization tools and tips: Ultimate guide [2025]](https://www.flexera.com/blog/finops/aws-cost-optimization-8-tools-and-tips-to-reduce-your-cloud-costs/)


---

*Photo by [Nick Fewings](https://unsplash.com/@jannerboy62) on [Unsplash](https://unsplash.com/photos/a-blue-light-bulb-sitting-on-top-of-a-table-6ylliBJGhgk)*

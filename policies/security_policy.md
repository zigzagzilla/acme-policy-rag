# Information Security Policy

**Policy ID:** IT-001  
**Effective Date:** March 1, 2024  
**Owner:** Information Technology / CISO

---

## 1. Purpose

This policy defines Acme Corp's requirements for protecting information assets. All employees, contractors, and third parties with access to Acme Corp systems are required to comply with this policy.

## 2. Password Requirements

All accounts must use strong passwords meeting the following criteria:
- Minimum 12 characters in length
- At least one uppercase letter, one lowercase letter, one number, and one special character
- Passwords must not be reused for the previous 12 cycles
- Passwords must be changed every 90 days for privileged accounts; every 180 days for standard accounts

Multi-factor authentication (MFA) is **mandatory** for:
- All remote access (VPN, remote desktop)
- All cloud service accounts (Google Workspace, AWS, Azure)
- HR and financial systems

## 3. Acceptable Use of Company Systems

Company computers, networks, and accounts are provided for business purposes. Limited personal use is permitted provided it does not:
- Interfere with job performance
- Involve illegal, offensive, or inappropriate content
- Compromise the security of company systems

Employees must not install unauthorized software on company devices. All software installations must be approved through the IT Service Desk.

## 4. Data Classification

| Level | Description | Examples | Handling |
|---|---|---|---|
| Public | No restrictions | Marketing materials, job postings | No special handling |
| Internal | General company use | Policies, procedures, org charts | Internal sharing only |
| Confidential | Sensitive business data | Financial reports, contracts | Encrypted at rest and in transit |
| Restricted | Highest sensitivity | PII, credentials, legal matters | Strict access controls, logging |

## 5. Device Security

All company-owned devices must have:
- Full-disk encryption enabled
- Automatic screen lock after 5 minutes of inactivity
- Approved endpoint protection (antivirus/EDR) installed and up to date
- Automatic OS and security updates enabled

Employees must not connect to public Wi-Fi without using the company VPN. If a device is lost or stolen, it must be reported to IT immediately (ithelp@acmecorp.com) so remote wipe can be initiated.

## 6. Phishing and Social Engineering

Employees must not click links, open attachments, or provide credentials in response to unsolicited emails or messages. Suspected phishing emails must be reported to security@acmecorp.com using the "Report Phishing" button in Gmail.

Acme Corp will never ask for your password via email, chat, or phone.

## 7. Incident Reporting

Security incidents, including suspected breaches, unauthorized access, or data exposure, must be reported within 1 hour of discovery to security@acmecorp.com and the employee's manager. Failure to report known security incidents is a policy violation subject to disciplinary action.

## 8. Remote Access

Remote work requires the use of the company VPN (GlobalProtect). Access to sensitive systems from personal devices is prohibited unless the device is enrolled in the company MDM program.

## 9. Compliance and Consequences

Violations of this policy may result in disciplinary action up to and including termination and legal prosecution. The IT Security team conducts periodic audits of system access and usage logs.

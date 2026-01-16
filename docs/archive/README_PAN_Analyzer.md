# PAN Skynet Analyzer

A comprehensive security rule analysis tool for Palo Alto Networks firewalls that identifies potential issues, optimization opportunities, and security risks in your rulebase.

## Features

- **Security Rule Analysis**: Analyzes all security rules for common issues and misconfigurations
- **Issue Detection**: Identifies disabled rules, any-any rules, missing logging, and more
- **Shadow Rule Detection**: Finds rules that will never be evaluated due to rule ordering
- **Redundancy Analysis**: Identifies redundant rules that can be consolidated
- **Comprehensive Reporting**: Generates detailed reports in both text and JSON formats
- **Modular Design**: Easy to extend and customize for specific needs

## Issues Detected

### 🔴 Critical Issues
- **Shadowed Rules**: Rules that will never be evaluated due to rule ordering
- **Redundant Rules**: Rules that duplicate functionality of other rules

### 🟡 Warnings
- **Any-Any Rules**: Rules allowing traffic from any source to any destination
- **Missing Logging**: Rules without logging configuration
- **Missing Security Profiles**: Rules without security profile groups assigned

### ℹ️ Informational
- **Disabled Rules**: Rules that are currently disabled

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional):
```bash
export PAN_FIREWALL_IP="your_firewall_ip"
export PAN_API_KEY="your_api_key"
```

## Usage

### Basic Usage

Run the analyzer with interactive input:
```bash
python pan_skynet_analyzer.py
```

### With Environment Variables

Set your firewall IP and API key as environment variables:
```bash
export PAN_FIREWALL_IP="192.168.1.1"
export PAN_API_KEY="your_api_key_here"
python pan_skynet_analyzer.py
```

### Testing

Run the test script to verify functionality:
```bash
python test_pan_analyzer.py
```

## API Key Generation

To generate an API key for your PAN firewall:

1. Log into the PAN firewall web interface
2. Go to **Device** > **Setup** > **Management** > **Management Interface Settings**
3. Enable **API Key** service
4. Go to **Device** > **Setup** > **Management** > **API Key Management**
5. Generate a new API key for your user

## Output Files

The analyzer generates two output files:

1. **Text Report** (`pan_analysis_report_YYYYMMDD_HHMMSS.txt`):
   - Human-readable analysis report
   - Summary statistics
   - Detailed issue descriptions
   - Actionable recommendations

2. **JSON Report** (`pan_analysis_report_YYYYMMDD_HHMMSS.json`):
   - Machine-readable format
   - Complete analysis data
   - Suitable for automation and integration

## Analysis Categories

### Rulebase Health
- Total number of rules analyzed
- Count of disabled rules
- Identification of any-any rules
- Rules without proper logging
- Rules without security profiles

### Security Issues
- Shadowed rules (rules that will never be hit)
- Redundant rules (duplicate functionality)
- Overly permissive rules
- Missing security controls

### Optimization Opportunities
- Rule consolidation recommendations
- Cleanup suggestions
- Performance optimization tips

## Example Output

```
============================================================
PAN SKYNET ANALYZER - SECURITY RULE ANALYSIS REPORT
============================================================
Generated: 2025-08-20 16:26:38

SUMMARY:
--------------------
Total Rules Analyzed: 3
Disabled Rules: 1
Any-Any Rules: 1
Rules Without Logging: 1
Rules Without Security Profiles: 1
Shadowed Rules: 2
Redundant Rules: 2

ISSUES FOUND:
--------------------
🔴 Rule 'Any-Any-Rule' is shadowed by a previous rule
🟡 Rule 'Any-Any-Rule' allows traffic from any source to any destination using any application
🟡 Rule 'Any-Any-Rule' has no log setting configured
🟡 Rule 'Any-Any-Rule' has no security profile group assigned
🟡 Rule 'Any-Any-Rule' may be redundant with: Allow-Web
ℹ️ Rule 'Disabled-Rule' is disabled

RECOMMENDATIONS:
--------------------
1. Review and remove disabled rules to clean up the rulebase
2. Replace 'any-any' rules with more specific rules for better security
3. Configure logging for all rules to enable proper monitoring and troubleshooting
4. Assign security profiles to all rules for threat prevention and content filtering
5. Remove or reorder shadowed rules that will never be evaluated
6. Consolidate redundant rules to simplify management and improve performance
```

## Architecture

The tool consists of several key components:

- **PANAPI Class**: Handles communication with the PAN firewall API
- **RuleAnalyzer Class**: Contains the core analysis logic
- **Analysis Functions**: Modular functions for different types of analysis
- **Reporting Functions**: Generate formatted output in multiple formats

## Extending the Analyzer

The modular design makes it easy to add new analysis types:

1. Add new analysis methods to the `RuleAnalyzer` class
2. Update the `_analyze_single_rule` method to call your new analysis
3. Add corresponding summary counters and issue types
4. Update the recommendations generation logic

## Security Considerations

- API keys should be stored securely (use environment variables or secure vaults)
- The tool disables SSL verification for self-signed certificates
- Network access to the firewall management interface is required
- The tool only reads configuration data (no modifications are made)

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check firewall IP address and network connectivity
2. **Authentication Failed**: Verify API key is correct and user has proper permissions
3. **No Rules Found**: Check that the user has permission to view security rules
4. **SSL Certificate Errors**: The tool automatically handles self-signed certificates

### Debug Mode

Enable debug logging by modifying the logging level in the script:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

## License

This tool is provided as-is for educational and operational purposes. Please ensure compliance with your organization's security policies when using this tool.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the tool.
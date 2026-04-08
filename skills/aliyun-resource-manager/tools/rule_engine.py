#!/usr/bin/env python3
"""
Rule Engine for Aliyun Resource Manager

Loads and evaluates YAML rules against resources.
Supports user-defined rules (./rules/) and built-in rules.
"""

import yaml
import logging
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Rule:
    """Represents a single rule."""

    def __init__(self, rule_data: Dict[str, Any]):
        self.id = rule_data.get('id', 'unknown')
        self.name = rule_data.get('name', 'Unknown Rule')
        self.resource = rule_data.get('resource', '')
        self.condition = rule_data.get('condition', '')
        self.severity = rule_data.get('severity', 'info')
        self.description = rule_data.get('description', '')

    def evaluate(self, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluate rule against a resource.

        Args:
            resource: Resource data to check

        Returns:
            Violation details if rule matches, None otherwise
        """
        try:
            if self._check_condition(resource):
                return {
                    'rule_id': self.id,
                    'rule_name': self.name,
                    'severity': self.severity,
                    'description': self.description,
                    'resource_id': resource.get('id', 'unknown'),
                    'resource_name': resource.get('name', 'unknown'),
                    'resource_type': self.resource
                }
        except Exception as e:
            logger.error(f"Error evaluating rule {self.id}: {e}")

        return None

    def _check_condition(self, resource: Dict[str, Any]) -> bool:
        """
        Parse and check condition against resource.

        Supported condition patterns:
        - name !~ /pattern/ : name does not match regex
        - name =~ /pattern/ : name matches regex
        - ports contains [22,33] : ports list contains specified ports
        - source = 0.0.0.0/0 : exact match
        - status = value : status equals value
        - cpu_avg_24h < 10 : numeric comparison
        """
        condition = self.condition.strip()

        # Handle regex patterns (name !~ /pattern/ or name =~ /pattern/)
        if '!~' in condition or '=~' in condition:
            return self._check_regex_condition(resource, condition)

        # Handle contains
        if 'contains' in condition:
            return self._check_contains_condition(resource, condition)

        # Handle numeric comparisons
        if any(op in condition for op in ['<', '>', '<=', '>=']):
            return self._check_numeric_condition(resource, condition)

        # Handle equality
        if '=' in condition:
            return self._check_equality_condition(resource, condition)

        return False

    def _check_regex_condition(self, resource: Dict[str, Any], condition: str) -> bool:
        """Check regex-based condition."""
        # Parse: name !~ /pattern/ or name =~ /pattern/
        if '!~' in condition:
            field, pattern = condition.split('!~', 1)
            negate = True
        else:
            field, pattern = condition.split('=~', 1)
            negate = False

        field = field.strip()
        pattern = pattern.strip().strip('/')

        value = resource.get(field, '')
        if isinstance(value, (int, float)):
            value = str(value)

        matches = bool(re.search(pattern, value))
        return not matches if negate else matches

    def _check_contains_condition(self, resource: Dict[str, Any], condition: str) -> bool:
        """Check contains condition for ports."""
        # Parse: ports contains [22,33,44]
        match = re.match(r'(\w+)\s+contains\s+\[(.*?)\]', condition)
        if not match:
            return False

        field = match.group(1)
        values_str = match.group(2)

        try:
            check_values = [int(v.strip()) for v in values_str.split(',')]
        except ValueError:
            check_values = [v.strip() for v in values_str.split(',')]

        resource_value = resource.get(field, [])
        if not isinstance(resource_value, list):
            resource_value = [resource_value]

        return any(v in resource_value for v in check_values)

    def _check_numeric_condition(self, resource: Dict[str, Any], condition: str) -> bool:
        """Check numeric comparison condition."""
        # Parse: cpu_avg_24h < 10
        match = re.match(r'(\w+)\s*([<>]=?)\s*(\d+)', condition)
        if not match:
            return False

        field = match.group(1)
        operator = match.group(2)
        threshold = float(match.group(3))

        value = resource.get(field, 0)
        if isinstance(value, str):
            # Try to extract numeric value (e.g., "5.2%" -> 5.2)
            match = re.search(r'[\d.]+', value)
            value = float(match.group()) if match else 0

        if operator == '<':
            return value < threshold
        elif operator == '>':
            return value > threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '>=':
            return value >= threshold

        return False

    def _check_equality_condition(self, resource: Dict[str, Any], condition: str) -> bool:
        """Check equality condition."""
        # Parse: status = unused or source = 0.0.0.0/0
        field, value = condition.split('=', 1)
        field = field.strip()
        value = value.strip().strip('"').strip("'")

        resource_value = resource.get(field, '')
        return str(resource_value) == value


class RuleEngine:
    """Manages and evaluates rules."""

    def __init__(self):
        self.rules: List[Rule] = []
        self.user_rules_dir = Path('./rules')
        self.builtin_rules_dir = Path(__file__).parent.parent / 'rules'

    def load_rules(self) -> None:
        """
        Load rules from user directory first, then builtin.
        User rules take precedence.
        """
        self.rules = []
        loaded_ids = set()

        # Load user rules first (if directory exists)
        if self.user_rules_dir.exists():
            logger.info(f"Loading user rules from {self.user_rules_dir}")
            for rule_file in sorted(self.user_rules_dir.glob('*.yaml')):
                self._load_rule_file(rule_file, loaded_ids)

        # Load builtin rules
        if self.builtin_rules_dir.exists():
            logger.info(f"Loading builtin rules from {self.builtin_rules_dir}")
            for rule_file in sorted(self.builtin_rules_dir.glob('*.yaml')):
                self._load_rule_file(rule_file, loaded_ids)

        logger.info(f"Loaded {len(self.rules)} rules total")

    def _load_rule_file(self, filepath: Path, loaded_ids: set) -> None:
        """Load rules from a single YAML file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'rules' not in data:
                logger.warning(f"No rules found in {filepath}")
                return

            for rule_data in data['rules']:
                rule_id = rule_data.get('id')
                if not rule_id:
                    continue

                # Skip if already loaded (user rules take precedence)
                if rule_id in loaded_ids:
                    logger.debug(f"Skipping duplicate rule: {rule_id}")
                    continue

                self.rules.append(Rule(rule_data))
                loaded_ids.add(rule_id)
                logger.debug(f"Loaded rule: {rule_id}")

            logger.info(f"Loaded rules from {filepath.name}")

        except Exception as e:
            logger.error(f"Failed to load rules from {filepath}: {e}")

    def evaluate_resource(self, resource: Dict[str, Any], resource_type: str) -> List[Dict[str, Any]]:
        """
        Evaluate all rules against a single resource.

        Args:
            resource: Resource data
            resource_type: Type of resource (ecs, vpc, etc.)

        Returns:
            List of violations
        """
        violations = []

        for rule in self.rules:
            if rule.resource == resource_type:
                violation = rule.evaluate(resource)
                if violation:
                    violations.append(violation)

        return violations

    def evaluate_resources(self, resources: List[Dict[str, Any]], resource_type: str) -> List[Dict[str, Any]]:
        """
        Evaluate all rules against multiple resources.

        Args:
            resources: List of resource data
            resource_type: Type of resources

        Returns:
            List of all violations
        """
        all_violations = []

        for resource in resources:
            violations = self.evaluate_resource(resource, resource_type)
            all_violations.extend(violations)

        return all_violations

    def get_rules_summary(self) -> Dict[str, int]:
        """Get summary of loaded rules."""
        summary = {}
        for rule in self.rules:
            resource = rule.resource
            summary[resource] = summary.get(resource, 0) + 1
        return summary


def main():
    """Main entry point for testing."""
    engine = RuleEngine()
    engine.load_rules()

    # Print loaded rules summary
    summary = engine.get_rules_summary()
    print("Loaded Rules Summary:")
    for resource, count in sorted(summary.items()):
        print(f"  {resource}: {count} rules")

    # Test evaluation
    test_resources = [
        {'id': 'ecs-001', 'name': 'web-server', 'cpu_avg_24h': '5.2%'},
        {'id': 'ecs-002', 'name': 'user-00123456-app', 'cpu_avg_24h': '25%'}
    ]

    print("\nTest Evaluation Results:")
    violations = engine.evaluate_resources(test_resources, 'ecs')
    for v in violations:
        print(f"  {v['resource_id']}: {v['rule_name']} ({v['severity']})")


if __name__ == "__main__":
    main()

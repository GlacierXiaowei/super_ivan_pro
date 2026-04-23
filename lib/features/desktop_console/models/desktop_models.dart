class DesktopSnapshot {
  const DesktopSnapshot({
    required this.serviceStatusLabel,
    required this.activeTargetLabel,
    required this.rulePattern,
  });

  final String serviceStatusLabel;
  final String activeTargetLabel;
  final String rulePattern;
}

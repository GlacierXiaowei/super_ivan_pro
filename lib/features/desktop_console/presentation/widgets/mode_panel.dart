import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class ModePanel extends StatelessWidget {
  const ModePanel({
    super.key,
    required this.snapshot,
    required this.onModeChanged,
  });

  final DesktopSnapshot snapshot;
  final ValueChanged<DesktopMode> onModeChanged;

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '模式配置',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('极速模式'),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ChoiceChip(
                label: const Text('普通模式'),
                selected: snapshot.mode == DesktopMode.normal,
                onSelected: (_) => onModeChanged(DesktopMode.normal),
              ),
              ChoiceChip(
                label: const Text('极速模式'),
                selected: snapshot.mode == DesktopMode.rapid,
                onSelected: (_) => onModeChanged(DesktopMode.rapid),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

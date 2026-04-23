import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class StatusPanel extends StatelessWidget {
  const StatusPanel({super.key, required this.snapshot});

  final DesktopSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '服务状态',
      child: Wrap(
        spacing: 12,
        runSpacing: 12,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Chip(label: Text(snapshot.serviceStatusLabel)),
          Chip(label: Text(snapshot.armed ? 'armed' : 'disarmed')),
          Chip(
            label: Text(
              snapshot.mode == DesktopMode.rapid ? '极速模式' : '普通模式',
            ),
          ),
        ],
      ),
    );
  }
}

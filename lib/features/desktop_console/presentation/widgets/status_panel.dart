import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class StatusPanel extends StatelessWidget {
  const StatusPanel({
    super.key,
    required this.snapshot,
    required this.isBusy,
    required this.onStartPressed,
    required this.onStopPressed,
  });

  final DesktopSnapshot snapshot;
  final bool isBusy;
  final Future<void> Function() onStartPressed;
  final Future<void> Function() onStopPressed;

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '服务状态',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
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
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton(
                onPressed: isBusy ? null : () => onStartPressed(),
                child: const Text('启动服务'),
              ),
              OutlinedButton(
                onPressed: isBusy ? null : () => onStopPressed(),
                child: const Text('停止服务'),
              ),
            ],
          ),
          if (isBusy) ...[
            const SizedBox(height: 12),
            const LinearProgressIndicator(),
          ],
        ],
      ),
    );
  }
}

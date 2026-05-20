import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class StatusPanel extends StatelessWidget {
  const StatusPanel({
    super.key,
    required this.snapshot,
    required this.isBusy,
    required this.onStartPressed,
    required this.onRestartPressed,
    required this.onStopPressed,
    required this.onArmPressed,
    required this.onDisarmPressed,
  });

  final DesktopSnapshot snapshot;
  final bool isBusy;
  final Future<void> Function() onStartPressed;
  final Future<void> Function() onRestartPressed;
  final Future<void> Function() onStopPressed;
  final Future<void> Function() onArmPressed;
  final Future<void> Function() onDisarmPressed;

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
              Chip(label: Text('消息源: ${snapshot.watcherStateLabel}')),
              Chip(
                label: Text(snapshot.armState.enabled ? 'armed' : 'disarmed'),
              ),
              Chip(
                label: Text(
                  snapshot.mode == DesktopMode.rapid ? '极速模式' : '普通模式',
                ),
              ),
              Chip(
                label: Text(
                  '剩余触发: ${snapshot.armState.remainingTriggers ?? snapshot.armState.maxTriggers}',
                ),
              ),
            ],
          ),
          if (snapshot.watcherError.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              '消息源错误: ${snapshot.watcherError}',
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ],
          if (snapshot.armReason.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('监听状态原因: ${snapshot.armReason}'),
          ],
          if (snapshot.lastTriggerStatus.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('最近触发状态: ${snapshot.lastTriggerStatus}'),
          ],
          if (snapshot.lastError.isNotEmpty) ...[
            const SizedBox(height: 8),
            DecoratedBox(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  '最近发送错误: ${snapshot.lastError}',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onErrorContainer,
                  ),
                ),
              ),
            ),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton(
                onPressed: isBusy ? null : () => onStartPressed(),
                child: const Text('启动服务'),
              ),
              FilledButton.tonal(
                onPressed: isBusy ? null : () => onRestartPressed(),
                child: const Text('重启服务'),
              ),
              OutlinedButton(
                onPressed: isBusy ? null : () => onStopPressed(),
                child: const Text('停止服务'),
              ),
              FilledButton.tonal(
                onPressed: isBusy ? null : () => onArmPressed(),
                child: const Text('Arm'),
              ),
              OutlinedButton(
                onPressed: isBusy ? null : () => onDisarmPressed(),
                child: const Text('Disarm'),
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

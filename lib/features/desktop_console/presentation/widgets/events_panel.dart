import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class EventsPanel extends StatelessWidget {
  const EventsPanel({super.key, required this.snapshot});

  final DesktopSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '日志与事件',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('最近事件', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          if (snapshot.recentEvents.isEmpty)
            const Text('暂无最近事件')
          else
            ...snapshot.recentEvents.map(
              (event) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  '${event.chatName} / ${event.senderName}: ${event.content}',
                ),
              ),
            ),
          const SizedBox(height: 16),
          Text('运行日志', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          if (snapshot.recentLogs.isEmpty)
            const Text('暂无运行日志')
          else
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF0B1716),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: snapshot.recentLogs
                    .map(
                      (log) => Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: SelectableText(
                          '[${log.source}] ${log.message}',
                          style: const TextStyle(
                            color: Color(0xFFE0F2F1),
                            fontFamily: 'Consolas',
                            fontSize: 12,
                            height: 1.3,
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
        ],
      ),
    );
  }
}

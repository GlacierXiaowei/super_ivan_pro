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
        children: snapshot.recentEvents
            .map(
              (event) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  '${event.chatName} / ${event.senderName}: ${event.content}',
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}

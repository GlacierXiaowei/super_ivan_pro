import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class TargetPanel extends StatelessWidget {
  const TargetPanel({super.key, required this.snapshot});

  final DesktopSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '监听对象',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('当前对象：${snapshot.activeTarget.displayName}'),
          const SizedBox(height: 12),
          Text(
            '最近会话',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: snapshot.recentChats
                .map((chat) => Chip(label: Text(chat.label)))
                .toList(),
          ),
          const SizedBox(height: 12),
          Text(
            '手动输入监听对象',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          TextField(
            controller: TextEditingController(
              text: snapshot.activeTarget.displayName,
            ),
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              hintText: '输入群聊或联系人名称',
            ),
          ),
        ],
      ),
    );
  }
}

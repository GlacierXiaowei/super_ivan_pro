import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class RulePanel extends StatelessWidget {
  const RulePanel({super.key, required this.snapshot});

  final DesktopSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '规则配置',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('触发文本：${snapshot.rulePattern}'),
          const SizedBox(height: 8),
          const Text('匹配方式：精确 / 包含 / 正则'),
          const SizedBox(height: 8),
          const Text('回复消息：TEST / 第二条'),
        ],
      ),
    );
  }
}

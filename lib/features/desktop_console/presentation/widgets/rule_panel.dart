import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class RulePanel extends StatefulWidget {
  const RulePanel({
    super.key,
    required this.snapshot,
    required this.isBusy,
    required this.onSaveRule,
  });

  final DesktopSnapshot snapshot;
  final bool isBusy;
  final Future<void> Function({
    required String pattern,
    required List<String> replies,
    required int cooldownMs,
    required int maxTriggers,
    required DesktopMatchMode matchMode,
    required int replyDelayMs,
  })
  onSaveRule;

  @override
  State<RulePanel> createState() => _RulePanelState();
}

class _RulePanelState extends State<RulePanel> {
  late final TextEditingController _patternController;
  late final TextEditingController _repliesController;
  late final TextEditingController _cooldownController;
  late final TextEditingController _replyDelayController;
  late final TextEditingController _maxTriggersController;
  bool _isAnyTrigger = false;

  @override
  void initState() {
    super.initState();
    _patternController = TextEditingController();
    _repliesController = TextEditingController();
    _cooldownController = TextEditingController();
    _replyDelayController = TextEditingController();
    _maxTriggersController = TextEditingController();
    _syncFromSnapshot();
  }

  @override
  void didUpdateWidget(covariant RulePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.snapshot.rule.pattern != widget.snapshot.rule.pattern ||
        oldWidget.snapshot.rule.replies != widget.snapshot.rule.replies ||
        oldWidget.snapshot.rule.cooldownMs != widget.snapshot.rule.cooldownMs ||
        oldWidget.snapshot.rule.replyDelayMs !=
            widget.snapshot.rule.replyDelayMs ||
        oldWidget.snapshot.rule.matchMode != widget.snapshot.rule.matchMode ||
        oldWidget.snapshot.armState.maxTriggers !=
            widget.snapshot.armState.maxTriggers) {
      _syncFromSnapshot();
    }
  }

  void _syncFromSnapshot() {
    _patternController.text = widget.snapshot.rule.pattern;
    _repliesController.text = widget.snapshot.rule.replies.join('\n');
    _cooldownController.text = '${widget.snapshot.rule.cooldownMs}';
    _replyDelayController.text = '${widget.snapshot.rule.replyDelayMs}';
    _maxTriggersController.text = '${widget.snapshot.armState.maxTriggers}';
    _isAnyTrigger = widget.snapshot.rule.matchMode == DesktopMatchMode.any;
  }

  @override
  void dispose() {
    _patternController.dispose();
    _repliesController.dispose();
    _cooldownController.dispose();
    _replyDelayController.dispose();
    _maxTriggersController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '规则配置',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _patternController,
            enabled: !widget.isBusy && !_isAnyTrigger,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              labelText: '触发文本',
              helperText: '任意消息触发开启时，此字段不参与匹配',
            ),
          ),
          const SizedBox(height: 12),
          CheckboxListTile(
            value: _isAnyTrigger,
            enabled: !widget.isBusy,
            contentPadding: EdgeInsets.zero,
            title: const Text('任意消息触发'),
            subtitle: const Text('开启后，指定对象发文本、图片、表情、视频等任意消息都会触发'),
            onChanged: (value) {
              setState(() {
                _isAnyTrigger = value ?? false;
              });
            },
          ),
          const SizedBox(height: 12),
          const Text('普通模式匹配方式：正则'),
          const SizedBox(height: 12),
          TextField(
            controller: _repliesController,
            enabled: !widget.isBusy,
            maxLines: 3,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              labelText: '回复消息，每行一条',
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _cooldownController,
                  enabled: !widget.isBusy,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: '冷却毫秒',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _replyDelayController,
                  enabled: !widget.isBusy,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: '回复延迟毫秒',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _maxTriggersController,
                  enabled: !widget.isBusy,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: '最大触发次数',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton(
              onPressed: widget.isBusy
                  ? null
                  : () => widget.onSaveRule(
                      pattern: _patternController.text.trim(),
                      replies: _repliesController.text
                          .split('\n')
                          .map((line) => line.trim())
                          .where((line) => line.isNotEmpty)
                          .toList(),
                      cooldownMs:
                          int.tryParse(_cooldownController.text.trim()) ?? 0,
                      maxTriggers:
                          int.tryParse(_maxTriggersController.text.trim()) ?? 1,
                      matchMode: _isAnyTrigger
                          ? DesktopMatchMode.any
                          : DesktopMatchMode.regex,
                      replyDelayMs:
                          int.tryParse(_replyDelayController.text.trim()) ?? 0,
                    ),
              child: const Text('保存规则'),
            ),
          ),
        ],
      ),
    );
  }
}

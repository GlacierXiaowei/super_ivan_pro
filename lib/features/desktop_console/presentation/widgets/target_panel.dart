import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class TargetPanel extends StatefulWidget {
  const TargetPanel({
    super.key,
    required this.snapshot,
    required this.isBusy,
    required this.onSaveTarget,
  });

  final DesktopSnapshot snapshot;
  final bool isBusy;
  final Future<void> Function({
    required String displayName,
    required String talker,
    required bool isGroup,
  })
  onSaveTarget;

  @override
  State<TargetPanel> createState() => _TargetPanelState();
}

class _TargetPanelState extends State<TargetPanel> {
  late final TextEditingController _controller;
  bool _isGroup = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(
      text: widget.snapshot.activeTarget.displayName,
    );
    _isGroup = widget.snapshot.activeTarget.isGroup;
  }

  @override
  void didUpdateWidget(covariant TargetPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.snapshot.activeTarget.displayName !=
        widget.snapshot.activeTarget.displayName) {
      _controller.text = widget.snapshot.activeTarget.displayName;
      _isGroup = widget.snapshot.activeTarget.isGroup;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PanelCard(
      title: '监听对象',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('当前对象：${widget.snapshot.activeTarget.displayName}'),
          const SizedBox(height: 12),
          Text(
            '最近会话',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: widget.snapshot.recentChats
                .map(
                  (chat) => ActionChip(
                    label: Text(chat.label),
                    onPressed: widget.isBusy
                        ? null
                        : () async {
                            _controller.text = chat.label;
                            setState(() {
                              _isGroup = chat.isGroup;
                            });
                            await widget.onSaveTarget(
                              displayName: chat.label,
                              talker: chat.talker,
                              isGroup: chat.isGroup,
                            );
                          },
                  ),
                )
                .toList(),
          ),
          const SizedBox(height: 12),
          Text(
            '手动输入监听对象',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _controller,
            enabled: !widget.isBusy,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              hintText: '输入群聊或联系人名称',
            ),
          ),
          const SizedBox(height: 8),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            value: _isGroup,
            title: const Text('按群聊处理'),
            onChanged: widget.isBusy
                ? null
                : (value) {
                    setState(() {
                      _isGroup = value ?? false;
                    });
                  },
          ),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton(
              onPressed: widget.isBusy
                  ? null
                  : () => widget.onSaveTarget(
                        displayName: _controller.text.trim(),
                        talker: _controller.text.trim(),
                        isGroup: _isGroup,
                      ),
              child: const Text('保存对象'),
            ),
          ),
        ],
      ),
    );
  }
}

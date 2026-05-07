import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/panel_card.dart';

class TargetPanel extends StatefulWidget {
  const TargetPanel({
    super.key,
    required this.snapshot,
    required this.isBusy,
    required this.onSaveTarget,
    required this.onSearchHistoryChats,
    required this.onSearchHistorySenders,
    required this.onSelectSender,
  });

  final DesktopSnapshot snapshot;
  final bool isBusy;
  final Future<void> Function({
    required String displayName,
    required String talker,
    required bool isGroup,
  })
  onSaveTarget;
  final Future<List<HistoryChatCandidate>> Function({required String query})
  onSearchHistoryChats;
  final Future<List<HistorySenderCandidate>> Function({
    required String chat,
    required String query,
  })
  onSearchHistorySenders;
  final Future<void> Function({
    required String sender,
    required String senderName,
  })
  onSelectSender;

  @override
  State<TargetPanel> createState() => _TargetPanelState();
}

class _TargetPanelState extends State<TargetPanel> {
  late final TextEditingController _controller;
  late final TextEditingController _chatSearchController;
  late final TextEditingController _memberSearchController;
  bool _isGroup = false;
  bool _isSearchingChats = false;
  bool _isSearchingMembers = false;
  String _chatSearchError = '';
  String _memberSearchError = '';
  List<HistoryChatCandidate> _chatCandidates = const [];
  List<HistorySenderCandidate> _memberCandidates = const [];

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(
      text: widget.snapshot.activeTarget.displayName,
    );
    _chatSearchController = TextEditingController();
    _memberSearchController = TextEditingController();
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
    _chatSearchController.dispose();
    _memberSearchController.dispose();
    super.dispose();
  }

  Future<void> _searchHistoryChats() async {
    setState(() {
      _isSearchingChats = true;
      _chatSearchError = '';
    });
    try {
      final candidates = await widget.onSearchHistoryChats(
        query: _chatSearchController.text.trim(),
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _chatCandidates = candidates;
        _chatSearchError = candidates.isEmpty ? '未找到匹配的历史群聊' : '';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _chatCandidates = const [];
        _chatSearchError = '$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSearchingChats = false;
        });
      }
    }
  }

  Future<void> _searchHistoryMembers() async {
    final chat = widget.snapshot.activeTarget.talker.trim();
    if (chat.isEmpty) {
      setState(() {
        _memberSearchError = '请先保存或选择一个群聊对象';
        _memberCandidates = const [];
      });
      return;
    }

    setState(() {
      _isSearchingMembers = true;
      _memberSearchError = '';
    });
    try {
      final candidates = await widget.onSearchHistorySenders(
        chat: chat,
        query: _memberSearchController.text.trim(),
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _memberCandidates = candidates;
        _memberSearchError = candidates.isEmpty ? '未找到匹配的历史发言人' : '';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _memberCandidates = const [];
        _memberSearchError = '$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSearchingMembers = false;
        });
      }
    }
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
          Text('最近会话', style: Theme.of(context).textTheme.titleSmall),
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
          const SizedBox(height: 16),
          Text('历史群聊搜索', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const ValueKey('history-chat-search-field'),
                  controller: _chatSearchController,
                  enabled: !widget.isBusy && !_isSearchingChats,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: '群名 / 群聊 ID 关键字',
                    helperText: '从历史会话和联系人缓存里查找 @chatroom',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              FilledButton.tonal(
                key: const ValueKey('history-chat-search-button'),
                onPressed: widget.isBusy || _isSearchingChats
                    ? null
                    : _searchHistoryChats,
                child: Text(_isSearchingChats ? '搜索中' : '搜索'),
              ),
            ],
          ),
          if (_chatSearchError.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              _chatSearchError,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ],
          if (_chatCandidates.isNotEmpty) ...[
            const SizedBox(height: 8),
            ..._chatCandidates.map(
              (candidate) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  dense: true,
                  title: Text(
                    candidate.displayName.isEmpty
                        ? candidate.talker
                        : candidate.displayName,
                  ),
                  subtitle: Text(
                    '${candidate.talker}\n最近: ${candidate.summary.isEmpty ? '暂无摘要' : candidate.summary}',
                  ),
                  isThreeLine: true,
                  trailing: TextButton(
                    onPressed: widget.isBusy
                        ? null
                        : () async {
                            final displayName = candidate.displayName.isEmpty
                                ? candidate.talker
                                : candidate.displayName;
                            _controller.text = displayName;
                            setState(() {
                              _isGroup = true;
                            });
                            await widget.onSaveTarget(
                              displayName: displayName,
                              talker: candidate.talker,
                              isGroup: true,
                            );
                          },
                    child: const Text('使用'),
                  ),
                ),
              ),
            ),
          ],
          const SizedBox(height: 12),
          Text('手动输入监听对象', style: Theme.of(context).textTheme.titleSmall),
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
          const SizedBox(height: 16),
          Text('历史群成员搜索', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Text(_senderFilterLabel(widget.snapshot.rule)),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _memberSearchController,
                  enabled: !widget.isBusy && !_isSearchingMembers,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: '成员昵称 / 备注 / ID 关键字',
                    helperText: '会从当前群聊历史发言里查找真实 sender ID',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              FilledButton.tonal(
                onPressed: widget.isBusy || _isSearchingMembers
                    ? null
                    : _searchHistoryMembers,
                child: Text(_isSearchingMembers ? '搜索中' : '搜索'),
              ),
            ],
          ),
          if (widget.snapshot.rule.sender.isNotEmpty) ...[
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: widget.isBusy
                  ? null
                  : () => widget.onSelectSender(sender: '', senderName: ''),
              child: const Text('清除成员过滤'),
            ),
          ],
          if (_memberSearchError.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              _memberSearchError,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ],
          if (_memberCandidates.isNotEmpty) ...[
            const SizedBox(height: 8),
            ..._memberCandidates.map(
              (candidate) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  dense: true,
                  title: Text(
                    candidate.senderName.isEmpty
                        ? candidate.sender
                        : candidate.senderName,
                  ),
                  subtitle: Text(
                    '${candidate.sender}\n最近: ${candidate.lastContent}',
                  ),
                  isThreeLine: true,
                  trailing: TextButton(
                    onPressed: widget.isBusy
                        ? null
                        : () => widget.onSelectSender(
                            sender: candidate.sender,
                            senderName: candidate.senderName,
                          ),
                    child: const Text('使用'),
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _senderFilterLabel(DesktopRule rule) {
    if (rule.sender.isEmpty) {
      return '当前成员过滤：未限制';
    }
    final display = rule.senderName.isEmpty ? rule.sender : rule.senderName;
    return '当前成员过滤：$display (${rule.sender})';
  }
}

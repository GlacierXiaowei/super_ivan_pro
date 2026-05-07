enum DesktopMode { normal, rapid }

enum DesktopMatchMode { exact, contains, regex, any }

class ActiveTarget {
  const ActiveTarget({
    required this.displayName,
    required this.talker,
    required this.isGroup,
  });

  final String displayName;
  final String talker;
  final bool isGroup;

  Map<String, dynamic> toJson() {
    return {'display_name': displayName, 'talker': talker, 'is_group': isGroup};
  }
}

class DesktopRule {
  const DesktopRule({
    required this.pattern,
    required this.replies,
    required this.cooldownMs,
    this.replyDelayMs = 0,
    this.matchMode = DesktopMatchMode.regex,
    this.talker = '',
    this.isGroup = false,
    this.sender = '',
    this.senderName = '',
  });

  final String pattern;
  final List<String> replies;
  final int cooldownMs;
  final int replyDelayMs;
  final DesktopMatchMode matchMode;
  final String talker;
  final bool isGroup;
  final String sender;
  final String senderName;

  Map<String, dynamic> toRulePayload() {
    return {
      'id': 'desktop_rule',
      'enabled': true,
      'talker': talker,
      'sender': sender,
      'sender_name': senderName,
      'chat_scope': isGroup ? 'group' : 'private',
      'type': matchMode == DesktopMatchMode.any ? 'unknown' : 'text',
      'pattern': pattern,
      'replies': replies,
      'cooldown_ms': cooldownMs,
      'reply_delay_ms': replyDelayMs,
      'match_mode': matchMode.name,
    };
  }

  DesktopRule copyWith({
    String? pattern,
    List<String>? replies,
    int? cooldownMs,
    int? replyDelayMs,
    DesktopMatchMode? matchMode,
    String? talker,
    bool? isGroup,
    String? sender,
    String? senderName,
  }) {
    return DesktopRule(
      pattern: pattern ?? this.pattern,
      replies: replies ?? this.replies,
      cooldownMs: cooldownMs ?? this.cooldownMs,
      replyDelayMs: replyDelayMs ?? this.replyDelayMs,
      matchMode: matchMode ?? this.matchMode,
      talker: talker ?? this.talker,
      isGroup: isGroup ?? this.isGroup,
      sender: sender ?? this.sender,
      senderName: senderName ?? this.senderName,
    );
  }
}

class DesktopArmState {
  const DesktopArmState({
    required this.enabled,
    required this.maxTriggers,
    this.remainingTriggers,
  });

  final bool enabled;
  final int maxTriggers;
  final int? remainingTriggers;

  Map<String, dynamic> toJson() {
    return {
      'enabled': enabled,
      'max_triggers': maxTriggers,
      'remaining_triggers': remainingTriggers,
    };
  }

  DesktopArmState copyWith({
    bool? enabled,
    int? maxTriggers,
    int? remainingTriggers,
  }) {
    return DesktopArmState(
      enabled: enabled ?? this.enabled,
      maxTriggers: maxTriggers ?? this.maxTriggers,
      remainingTriggers: remainingTriggers ?? this.remainingTriggers,
    );
  }
}

class RecentChatPreview {
  const RecentChatPreview({
    required this.label,
    required this.talker,
    required this.isGroup,
  });

  final String label;
  final String talker;
  final bool isGroup;
}

class RecentEventPreview {
  const RecentEventPreview({
    required this.chatName,
    required this.senderName,
    required this.content,
  });

  final String chatName;
  final String senderName;
  final String content;
}

class HistoryChatCandidate {
  const HistoryChatCandidate({
    required this.talker,
    required this.displayName,
    required this.lastTimestamp,
    required this.summary,
    required this.source,
  });

  factory HistoryChatCandidate.fromJson(Map<String, dynamic> json) {
    return HistoryChatCandidate(
      talker: json['talker'] as String? ?? '',
      displayName: json['display_name'] as String? ?? '',
      lastTimestamp: json['last_timestamp'] as int? ?? 0,
      summary: json['summary'] as String? ?? '',
      source: json['source'] as String? ?? '',
    );
  }

  final String talker;
  final String displayName;
  final int lastTimestamp;
  final String summary;
  final String source;
}

class HistorySenderCandidate {
  const HistorySenderCandidate({
    required this.sender,
    required this.senderName,
    required this.lastTimestamp,
    required this.lastContent,
    required this.messageCount,
  });

  factory HistorySenderCandidate.fromJson(Map<String, dynamic> json) {
    return HistorySenderCandidate(
      sender: json['sender'] as String? ?? '',
      senderName: json['sender_name'] as String? ?? '',
      lastTimestamp: json['last_timestamp'] as int? ?? 0,
      lastContent: json['last_content'] as String? ?? '',
      messageCount: json['message_count'] as int? ?? 0,
    );
  }

  final String sender;
  final String senderName;
  final int lastTimestamp;
  final String lastContent;
  final int messageCount;
}

class DesktopLogLine {
  const DesktopLogLine({required this.source, required this.message});

  final String source;
  final String message;
}

class DesktopSnapshot {
  const DesktopSnapshot({
    required this.serviceStatusLabel,
    required this.watcherStateLabel,
    required this.watcherError,
    required this.activeTarget,
    required this.recentChats,
    required this.recentEvents,
    required this.recentLogs,
    required this.mode,
    required this.rule,
    required this.armState,
  });

  factory DesktopSnapshot.seed() {
    return const DesktopSnapshot(
      serviceStatusLabel: 'running',
      watcherStateLabel: 'running',
      watcherError: '',
      activeTarget: ActiveTarget(
        displayName: '文件传输助手',
        talker: 'filehelper',
        isGroup: false,
      ),
      recentChats: [
        RecentChatPreview(
          label: '文件传输助手',
          talker: 'filehelper',
          isGroup: false,
        ),
        RecentChatPreview(label: '多姆斯利普🌙', talker: '多姆斯利普🌙', isGroup: true),
      ],
      recentEvents: [
        RecentEventPreview(
          chatName: '文件传输助手',
          senderName: '我',
          content: 'START',
        ),
      ],
      recentLogs: [
        DesktopLogLine(
          source: 'wechat_automation.log',
          message: 'rule_match rule=desktop_rule seq=1',
        ),
      ],
      mode: DesktopMode.normal,
      rule: DesktopRule(
        pattern: 'START',
        replies: ['TEST', '第二条'],
        cooldownMs: 800,
      ),
      armState: DesktopArmState(
        enabled: true,
        maxTriggers: 1,
        remainingTriggers: 1,
      ),
    );
  }

  factory DesktopSnapshot.offline() {
    return const DesktopSnapshot(
      serviceStatusLabel: '本地服务未启动',
      watcherStateLabel: 'unknown',
      watcherError: '',
      activeTarget: ActiveTarget(displayName: '', talker: '', isGroup: false),
      recentChats: [],
      recentEvents: [],
      recentLogs: [],
      mode: DesktopMode.normal,
      rule: DesktopRule(pattern: '', replies: [], cooldownMs: 0),
      armState: DesktopArmState(
        enabled: false,
        maxTriggers: 1,
        remainingTriggers: 1,
      ),
    );
  }

  factory DesktopSnapshot.fromJson(Map<String, dynamic> json) {
    final activeTarget = (json['active_target'] as Map?)
        ?.cast<String, dynamic>();
    final rules = ((json['rules'] as List?) ?? const [])
        .whereType<Map>()
        .map((item) => item.cast<String, dynamic>())
        .toList();
    final firstRule = rules.isNotEmpty ? rules.first : null;
    final recentEvents = ((json['recent_events'] as List?) ?? const [])
        .whereType<Map>()
        .map((item) => item.cast<String, dynamic>())
        .map(
          (item) => RecentEventPreview(
            chatName:
                item['chat_name'] as String? ??
                item['talker_name'] as String? ??
                '',
            senderName: item['sender_name'] as String? ?? '',
            content: item['content'] as String? ?? '',
          ),
        )
        .toList();
    final recentLogs = ((json['recent_logs'] as List?) ?? const [])
        .whereType<Map>()
        .map((item) => item.cast<String, dynamic>())
        .map(
          (item) => DesktopLogLine(
            source: item['source'] as String? ?? '',
            message: item['message'] as String? ?? '',
          ),
        )
        .toList();
    final recentChats = ((json['recent_chats'] as List?) ?? const []).map((
      item,
    ) {
      if (item is Map) {
        final payload = item.cast<String, dynamic>();
        return RecentChatPreview(
          label: payload['label'] as String? ?? '',
          talker: payload['talker'] as String? ?? '',
          isGroup: payload['is_group'] as bool? ?? false,
        );
      }
      final label = '$item';
      return RecentChatPreview(
        label: label,
        talker: label,
        isGroup: label.endsWith('@chatroom'),
      );
    }).toList();

    return DesktopSnapshot(
      serviceStatusLabel: json['service_state'] as String? ?? 'running',
      watcherStateLabel: json['watcher_state'] as String? ?? 'unknown',
      watcherError: json['watcher_error'] as String? ?? '',
      activeTarget: ActiveTarget(
        displayName: activeTarget?['display_name'] as String? ?? '',
        talker: activeTarget?['talker'] as String? ?? '',
        isGroup: activeTarget?['is_group'] as bool? ?? false,
      ),
      recentChats: recentChats,
      recentEvents: recentEvents,
      recentLogs: recentLogs,
      mode: json['mode'] == 'rapid' ? DesktopMode.rapid : DesktopMode.normal,
      rule: DesktopRule(
        pattern: json['rule_pattern'] as String? ?? '',
        replies: ((json['replies'] as List?) ?? const [])
            .map((item) => '$item')
            .toList(),
        cooldownMs: json['cooldown_ms'] as int? ?? 0,
        replyDelayMs: json['reply_delay_ms'] as int? ?? 0,
        matchMode: _parseMatchMode(json['match_mode'] as String?),
        talker: activeTarget?['talker'] as String? ?? '',
        isGroup: activeTarget?['is_group'] as bool? ?? false,
        sender:
            json['rule_sender'] as String? ??
            firstRule?['sender'] as String? ??
            '',
        senderName:
            json['rule_sender_name'] as String? ??
            firstRule?['sender_name'] as String? ??
            '',
      ),
      armState: DesktopArmState(
        enabled: json['armed'] as bool? ?? false,
        maxTriggers: json['max_triggers'] as int? ?? 1,
        remainingTriggers: json['remaining_triggers'] as int?,
      ),
    );
  }

  final String serviceStatusLabel;
  final String watcherStateLabel;
  final String watcherError;
  final ActiveTarget activeTarget;
  final List<RecentChatPreview> recentChats;
  final List<RecentEventPreview> recentEvents;
  final List<DesktopLogLine> recentLogs;
  final DesktopMode mode;
  final DesktopRule rule;
  final DesktopArmState armState;

  DesktopSnapshot copyWith({
    String? serviceStatusLabel,
    String? watcherStateLabel,
    String? watcherError,
    ActiveTarget? activeTarget,
    List<RecentChatPreview>? recentChats,
    List<RecentEventPreview>? recentEvents,
    List<DesktopLogLine>? recentLogs,
    DesktopMode? mode,
    DesktopRule? rule,
    DesktopArmState? armState,
  }) {
    return DesktopSnapshot(
      serviceStatusLabel: serviceStatusLabel ?? this.serviceStatusLabel,
      watcherStateLabel: watcherStateLabel ?? this.watcherStateLabel,
      watcherError: watcherError ?? this.watcherError,
      activeTarget: activeTarget ?? this.activeTarget,
      recentChats: recentChats ?? this.recentChats,
      recentEvents: recentEvents ?? this.recentEvents,
      recentLogs: recentLogs ?? this.recentLogs,
      mode: mode ?? this.mode,
      rule: rule ?? this.rule,
      armState: armState ?? this.armState,
    );
  }

  static DesktopMatchMode _parseMatchMode(String? value) {
    return switch (value) {
      'exact' => DesktopMatchMode.exact,
      'contains' => DesktopMatchMode.contains,
      'any' => DesktopMatchMode.any,
      _ => DesktopMatchMode.regex,
    };
  }
}

enum DesktopMode { normal, rapid }

class ActiveTarget {
  const ActiveTarget({
    required this.displayName,
    required this.talker,
    required this.isGroup,
  });

  final String displayName;
  final String talker;
  final bool isGroup;
}

class RecentChatPreview {
  const RecentChatPreview({
    required this.label,
    required this.talker,
  });

  final String label;
  final String talker;
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

class DesktopSnapshot {
  const DesktopSnapshot({
    required this.serviceStatusLabel,
    required this.activeTarget,
    required this.recentChats,
    required this.recentEvents,
    required this.armed,
    required this.mode,
    required this.rulePattern,
  });

  factory DesktopSnapshot.seed() {
    return const DesktopSnapshot(
      serviceStatusLabel: '本地服务未启动',
      activeTarget: ActiveTarget(
        displayName: '文件传输助手',
        talker: 'filehelper',
        isGroup: false,
      ),
      recentChats: [
        RecentChatPreview(label: '文件传输助手', talker: 'filehelper'),
        RecentChatPreview(label: '多姆斯利普🌙', talker: '多姆斯利普🌙'),
      ],
      recentEvents: [
        RecentEventPreview(
          chatName: '文件传输助手',
          senderName: '我',
          content: 'START',
        ),
      ],
      armed: true,
      mode: DesktopMode.normal,
      rulePattern: 'START',
    );
  }

  final String serviceStatusLabel;
  final ActiveTarget activeTarget;
  final List<RecentChatPreview> recentChats;
  final List<RecentEventPreview> recentEvents;
  final bool armed;
  final DesktopMode mode;
  final String rulePattern;

  DesktopSnapshot copyWith({
    String? serviceStatusLabel,
    ActiveTarget? activeTarget,
    List<RecentChatPreview>? recentChats,
    List<RecentEventPreview>? recentEvents,
    bool? armed,
    DesktopMode? mode,
    String? rulePattern,
  }) {
    return DesktopSnapshot(
      serviceStatusLabel: serviceStatusLabel ?? this.serviceStatusLabel,
      activeTarget: activeTarget ?? this.activeTarget,
      recentChats: recentChats ?? this.recentChats,
      recentEvents: recentEvents ?? this.recentEvents,
      armed: armed ?? this.armed,
      mode: mode ?? this.mode,
      rulePattern: rulePattern ?? this.rulePattern,
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/target_panel.dart';

void main() {
  testWidgets(
    'searches history chats and saves selected chat as group target',
    (tester) async {
      String? searchedQuery;
      String? savedDisplayName;
      String? savedTalker;
      bool? savedIsGroup;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: TargetPanel(
                snapshot: DesktopSnapshot.seed(),
                isBusy: false,
                onSaveTarget:
                    ({
                      required displayName,
                      required talker,
                      required isGroup,
                    }) async {
                      savedDisplayName = displayName;
                      savedTalker = talker;
                      savedIsGroup = isGroup;
                    },
                onSearchHistoryChats: ({required query}) async {
                  searchedQuery = query;
                  return const [
                    HistoryChatCandidate(
                      talker: '123456@chatroom',
                      displayName: '项目讨论群',
                      lastTimestamp: 1778000004,
                      summary: '最近一条群消息',
                      source: 'session',
                    ),
                  ];
                },
                onSearchHistorySenders:
                    ({required chat, required query}) async {
                      return const [];
                    },
                onSelectSender:
                    ({required sender, required senderName}) async {},
              ),
            ),
          ),
        ),
      );

      await tester.enterText(
        find.byKey(const ValueKey('history-chat-search-field')),
        '项目',
      );
      await tester.tap(
        find.byKey(const ValueKey('history-chat-search-button')),
      );
      await tester.pumpAndSettle();

      expect(searchedQuery, '项目');
      expect(find.text('项目讨论群'), findsOneWidget);
      expect(find.textContaining('123456@chatroom'), findsOneWidget);

      await tester.tap(find.widgetWithText(TextButton, '使用'));
      await tester.pumpAndSettle();

      expect(savedDisplayName, '项目讨论群');
      expect(savedTalker, '123456@chatroom');
      expect(savedIsGroup, isTrue);
    },
  );
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/rule_panel.dart';

void main() {
  testWidgets(
    'keeps local arbitrary trigger toggle across equivalent refresh',
    (tester) async {
      Future<void> pumpRule(DesktopRule rule) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: RulePanel(
                snapshot: DesktopSnapshot.seed().copyWith(rule: rule),
                isBusy: false,
                onSaveRule:
                    ({
                      required pattern,
                      required replies,
                      required cooldownMs,
                      required maxTriggers,
                      required matchMode,
                      required replyDelayMs,
                    }) async {},
              ),
            ),
          ),
        );
      }

      await pumpRule(
        DesktopRule(pattern: 'START', replies: ['TEST'], cooldownMs: 0),
      );
      await tester.tap(find.byType(CheckboxListTile));
      await tester.pump();
      expect(
        tester.widget<CheckboxListTile>(find.byType(CheckboxListTile)).value,
        isTrue,
      );

      await pumpRule(
        DesktopRule(pattern: 'START', replies: ['TEST'], cooldownMs: 0),
      );

      expect(
        tester.widget<CheckboxListTile>(find.byType(CheckboxListTile)).value,
        isTrue,
      );
    },
  );
}

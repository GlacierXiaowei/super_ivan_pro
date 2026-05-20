import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/status_panel.dart';

void main() {
  testWidgets('shows arm reason and latest send error', (tester) async {
    final snapshot = DesktopSnapshot.seed().copyWith(
      armReason: 'budget_exhausted',
      lastError: 'RuntimeError: foreground_not_wechat',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatusPanel(
            snapshot: snapshot,
            isBusy: false,
            onStartPressed: () async {},
            onRestartPressed: () async {},
            onStopPressed: () async {},
            onArmPressed: () async {},
            onDisarmPressed: () async {},
          ),
        ),
      ),
    );

    expect(find.text('监听状态原因: budget_exhausted'), findsOneWidget);
    expect(
      find.text('最近发送错误: RuntimeError: foreground_not_wechat'),
      findsOneWidget,
    );
  });
}

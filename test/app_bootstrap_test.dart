import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/app/app.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';

void main() {
  testWidgets('boots the windows desktop console shell', (tester) async {
    await tester.pumpWidget(
      SuperIvanDesktopApp(service: FakeDesktopService.seed()),
    );

    expect(find.text('微信自动化桌面端'), findsOneWidget);
    expect(find.text('服务状态'), findsOneWidget);
    expect(find.text('监听对象'), findsOneWidget);

    await tester.drag(find.byType(ListView), const Offset(0, -500));
    await tester.pumpAndSettle();

    expect(find.text('规则配置'), findsOneWidget);
  });
}

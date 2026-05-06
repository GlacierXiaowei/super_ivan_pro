import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/desktop_console_page.dart';

void main() {
  testWidgets('renders editable target and rule fields', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: DesktopConsolePage(service: FakeDesktopService.seed())),
    );
    await tester.pumpAndSettle();

    expect(find.text('最近会话'), findsOneWidget);
    expect(find.text('手动输入监听对象'), findsOneWidget);
    expect(find.text('历史群成员搜索'), findsOneWidget);
    expect(find.text('armed'), findsOneWidget);
    expect(find.text('保存对象'), findsOneWidget);
    expect(find.text('Arm'), findsOneWidget);
    expect(find.text('Disarm'), findsOneWidget);
    expect(find.text('重启服务'), findsOneWidget);
    expect(find.text('消息源: running'), findsOneWidget);

    await tester.scrollUntilVisible(
      find.byType(CheckboxListTile).first,
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();

    expect(find.text('任意消息触发'), findsOneWidget);
    expect(find.text('回复延迟毫秒'), findsOneWidget);
    expect(find.text('保存规则'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('模式配置'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    expect(find.text('模式配置'), findsOneWidget);

    await tester.scrollUntilVisible(
      find.textContaining('rule_match rule=desktop_rule seq=1'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    expect(
      find.textContaining('rule_match rule=desktop_rule seq=1'),
      findsWidgets,
    );
  });
}

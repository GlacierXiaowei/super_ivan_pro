import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/edition/module_registry.dart';

void main() {
  test('main edition registers no optional modules', () {
    expect(buildEditionModules(), isEmpty);
  });
}

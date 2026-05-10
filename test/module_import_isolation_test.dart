import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('main module host files do not import remote-control code', () {
    final guardedFiles = <String>[
      'lib/app/app.dart',
      'lib/core/modules/app_module.dart',
      'lib/core/modules/module_host_page.dart',
      'lib/edition/module_registry.dart',
    ];

    for (final path in guardedFiles) {
      final contents = File(path).readAsStringSync();

      expect(
        contents,
        isNot(contains('features/remote_control')),
        reason: '$path must not import a concrete remote-control module.',
      );
      expect(
        contents,
        isNot(contains('modules/remote_control')),
        reason: '$path must not import remote-control Python/module paths.',
      );
    }
  });
}

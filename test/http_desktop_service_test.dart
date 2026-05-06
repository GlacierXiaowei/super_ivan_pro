import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/data/http_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

void main() {
  test('loads desktop snapshot from local service status endpoint', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(server.close);

    server.listen((request) async {
      if (request.method == 'GET' && request.uri.path == '/status') {
        request.response
          ..statusCode = 200
          ..headers.contentType = ContentType.json
          ..write(
            jsonEncode({
              'service_state': 'running',
              'armed': true,
              'mode': 'rapid',
              'rule_pattern': 'START',
              'replies': ['TEST', '第二条'],
              'cooldown_ms': 800,
              'match_mode': 'regex',
              'active_target': {
                'display_name': '文件传输助手',
                'talker': 'filehelper',
                'is_group': false,
              },
              'recent_events': [
                {
                  'talker_name': '文件传输助手',
                  'sender_name': '我',
                  'content': 'START',
                },
              ],
              'recent_logs': [
                {
                  'source': 'wechat_automation.log',
                  'message': 'rule_match rule=desktop_rule seq=1',
                },
              ],
            }),
          );
        await request.response.close();
        return;
      }

      request.response.statusCode = 404;
      await request.response.close();
    });

    final service = HttpDesktopService(
      Uri.parse('http://${server.address.address}:${server.port}'),
    );

    final snapshot = await service.loadSnapshot();
    expect(snapshot.serviceStatusLabel, 'running');
    expect(snapshot.mode, DesktopMode.rapid);
    expect(snapshot.activeTarget.displayName, '文件传输助手');
    expect(snapshot.rule.replies, ['TEST', '第二条']);
    expect(snapshot.rule.cooldownMs, 800);
    expect(snapshot.recentEvents.single.chatName, '文件传输助手');
    expect(snapshot.recentLogs.single.source, 'wechat_automation.log');
    expect(
      snapshot.recentLogs.single.message,
      'rule_match rule=desktop_rule seq=1',
    );
  });

  test('posts mode updates to the local service', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(server.close);

    String? body;
    server.listen((request) async {
      if (request.method == 'POST' && request.uri.path == '/mode') {
        body = await utf8.decoder.bind(request).join();
        request.response
          ..statusCode = 200
          ..headers.contentType = ContentType.json
          ..write('{}');
        await request.response.close();
        return;
      }

      request.response.statusCode = 404;
      await request.response.close();
    });

    final service = HttpDesktopService(
      Uri.parse('http://${server.address.address}:${server.port}'),
    );

    await service.saveMode(DesktopMode.rapid);

    expect(body, contains('"mode":"rapid"'));
  });

  test('posts rule and arm state updates to the local service', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(server.close);

    final receivedBodies = <String>[];
    server.listen((request) async {
      if (request.method == 'POST' &&
          (request.uri.path == '/rules' || request.uri.path == '/arm-state')) {
        receivedBodies.add(await utf8.decoder.bind(request).join());
        request.response
          ..statusCode = 200
          ..headers.contentType = ContentType.json
          ..write('{}');
        await request.response.close();
        return;
      }

      request.response.statusCode = 404;
      await request.response.close();
    });

    final service = HttpDesktopService(
      Uri.parse('http://${server.address.address}:${server.port}'),
    );

    await service.saveRule(
      DesktopRule(pattern: 'START', replies: ['TEST', '第二条'], cooldownMs: 800),
    );
    await service.saveArmState(
      const DesktopArmState(
        enabled: true,
        maxTriggers: 1,
        remainingTriggers: 1,
      ),
    );

    expect(receivedBodies[0], contains('"pattern":"START"'));
    expect(receivedBodies[1], contains('"enabled":true'));
  });

  test('posts service restart to the local service', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(server.close);

    var restartCalled = false;
    server.listen((request) async {
      if (request.method == 'POST' && request.uri.path == '/services/restart') {
        restartCalled = true;
        request.response
          ..statusCode = 200
          ..headers.contentType = ContentType.json
          ..write('{}');
        await request.response.close();
        return;
      }

      request.response.statusCode = 404;
      await request.response.close();
    });

    final service = HttpDesktopService(
      Uri.parse('http://${server.address.address}:${server.port}'),
    );

    await service.restartServices();

    expect(restartCalled, isTrue);
  });
}

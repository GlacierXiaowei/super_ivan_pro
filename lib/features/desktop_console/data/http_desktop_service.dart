import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/data/windows_service_launcher.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class HttpDesktopService implements DesktopService {
  HttpDesktopService(
    this._baseUri, {
    HttpClient? client,
    WindowsServiceLauncher? launcher,
  }) : _client = client ?? HttpClient(),
       _launcher = launcher;

  factory HttpDesktopService.development() {
    const host = '127.0.0.1';
    const port = 18090;
    final pythonCommand = WindowsServiceLauncher.resolvePythonCommand();
    return HttpDesktopService(
      Uri.parse('http://$host:$port'),
      launcher: WindowsServiceLauncher(
        serviceRoot: WindowsServiceLauncher.resolveServiceRoot(),
        pythonExecutable: pythonCommand.executable,
        pythonArgumentsPrefix: pythonCommand.argumentsPrefix,
        host: host,
        port: port,
      ),
    );
  }

  final Uri _baseUri;
  final HttpClient _client;
  final WindowsServiceLauncher? _launcher;

  @override
  Future<DesktopSnapshot> loadSnapshot() async {
    try {
      final payload = await _requestJson('GET', '/status');
      return DesktopSnapshot.fromJson(payload);
    } on SocketException {
      if (_launcher == null) {
        return DesktopSnapshot.offline();
      }
      await _launcher.start();
      await _waitUntilAvailable();
      final payload = await _requestJson('GET', '/status');
      return DesktopSnapshot.fromJson(payload);
    } on HttpException {
      return DesktopSnapshot.offline();
    }
  }

  @override
  Future<DesktopSnapshot> saveTarget(ActiveTarget target) async {
    final payload = await _requestJsonWithLaunchRetry(
      'POST',
      '/targets/active',
      body: target.toJson(),
    );
    return DesktopSnapshot.fromJson(payload);
  }

  @override
  Future<DesktopSnapshot> saveRule(DesktopRule rule) async {
    final payload = await _requestJsonWithLaunchRetry(
      'POST',
      '/rules',
      body: {
        'rules': [rule.toRulePayload()],
      },
    );
    return DesktopSnapshot.fromJson(payload);
  }

  @override
  Future<DesktopSnapshot> saveArmState(DesktopArmState state) async {
    final payload = await _requestJsonWithLaunchRetry(
      'POST',
      '/arm-state',
      body: state.toJson(),
    );
    return DesktopSnapshot.fromJson(payload);
  }

  @override
  Future<DesktopSnapshot> saveMode(DesktopMode mode) async {
    final payload = await _requestJsonWithLaunchRetry(
      'POST',
      '/mode',
      body: {'mode': mode.name},
    );
    return DesktopSnapshot.fromJson(payload);
  }

  @override
  Future<List<HistorySenderCandidate>> searchHistorySenders({
    required String chat,
    required String query,
    int limit = 20,
  }) async {
    final uri = Uri(
      path: '/history/senders',
      queryParameters: {'chat': chat, 'query': query, 'limit': '$limit'},
    );
    final payload = await _requestJsonWithLaunchRetry('GET', uri.toString());
    return ((payload['candidates'] as List?) ?? const [])
        .whereType<Map>()
        .map((item) => item.cast<String, dynamic>())
        .map(HistorySenderCandidate.fromJson)
        .where((candidate) => candidate.sender.isNotEmpty)
        .toList();
  }

  @override
  Future<List<HistoryChatCandidate>> searchHistoryChats({
    required String query,
    int limit = 20,
  }) async {
    final uri = Uri(
      path: '/history/chats',
      queryParameters: {'query': query, 'limit': '$limit'},
    );
    final payload = await _requestJsonWithLaunchRetry('GET', uri.toString());
    return ((payload['candidates'] as List?) ?? const [])
        .whereType<Map>()
        .map((item) => item.cast<String, dynamic>())
        .map(HistoryChatCandidate.fromJson)
        .where((candidate) => candidate.talker.isNotEmpty)
        .toList();
  }

  @override
  Future<DesktopSnapshot> startServices() async {
    final payload = await _requestJsonWithLaunchRetry(
      'POST',
      '/services/start',
    );
    return DesktopSnapshot.fromJson(payload);
  }

  @override
  Future<DesktopSnapshot> restartServices() async {
    final payload = await _requestJsonWithLaunchRetry(
      'POST',
      '/services/restart',
    );
    return DesktopSnapshot.fromJson(payload);
  }

  @override
  Future<DesktopSnapshot> stopServices() async {
    final payload = await _requestJsonWithLaunchRetry('POST', '/services/stop');
    return DesktopSnapshot.fromJson(payload);
  }

  Future<Map<String, dynamic>> _requestJsonWithLaunchRetry(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    try {
      return await _requestJson(method, path, body: body);
    } on SocketException {
      final launcher = _launcher;
      if (launcher == null) {
        rethrow;
      }
      await launcher.start();
      await _waitUntilAvailable();
      return _requestJson(method, path, body: body);
    }
  }

  Future<void> _waitUntilAvailable() async {
    final deadline = DateTime.now().add(const Duration(seconds: 5));
    while (DateTime.now().isBefore(deadline)) {
      try {
        await _requestJson('GET', '/status');
        return;
      } on SocketException {
        await Future<void>.delayed(const Duration(milliseconds: 150));
      } on HttpException {
        await Future<void>.delayed(const Duration(milliseconds: 150));
      }
    }

    throw StateError('desktop_service_not_available');
  }

  Future<Map<String, dynamic>> _requestJson(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final request = switch (method) {
      'GET' => await _client.getUrl(_baseUri.resolve(path)),
      'POST' => await _client.postUrl(_baseUri.resolve(path)),
      _ => throw UnsupportedError('unsupported method: $method'),
    };

    if (body != null) {
      final encoded = utf8.encode(jsonEncode(body));
      request.headers.contentType = ContentType.json;
      request.contentLength = encoded.length;
      request.add(encoded);
    }

    final response = await request.close();
    final text = await response.transform(utf8.decoder).join();
    final payload = text.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(text) as Map<String, dynamic>;

    if (response.statusCode >= 400) {
      throw HttpException(
        'request failed: ${response.statusCode}',
        uri: _baseUri.resolve(path),
      );
    }

    return payload;
  }
}

import 'package:flutter/material.dart';
import 'package:super_ivan_pro/core/modules/app_module.dart';

class ModuleHostPage extends StatefulWidget {
  const ModuleHostPage({
    super.key,
    required this.desktopConsole,
    required this.modules,
  });

  final Widget desktopConsole;
  final List<AppModule> modules;

  @override
  State<ModuleHostPage> createState() => _ModuleHostPageState();
}

class _ModuleHostPageState extends State<ModuleHostPage> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final destinations = <NavigationRailDestination>[
      const NavigationRailDestination(
        icon: Icon(Icons.desktop_windows_outlined),
        selectedIcon: Icon(Icons.desktop_windows),
        label: Text('控制台'),
      ),
      for (final module in widget.modules)
        NavigationRailDestination(
          icon: Icon(module.icon),
          label: Text(module.title),
        ),
    ];
    final pages = <Widget>[
      widget.desktopConsole,
      for (final module in widget.modules) module.build(context),
    ];

    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _selectedIndex,
            labelType: NavigationRailLabelType.all,
            destinations: destinations,
            onDestinationSelected: (index) {
              setState(() {
                _selectedIndex = index;
              });
            },
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: IndexedStack(index: _selectedIndex, children: pages),
          ),
        ],
      ),
    );
  }
}

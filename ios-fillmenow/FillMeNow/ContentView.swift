import SwiftUI

struct ContentView: View {
    @State private var selection: Int

    init() {
        let args = ProcessInfo.processInfo.arguments
        if args.contains("-screenSaved") {
            _selection = State(initialValue: 1)
        } else if args.contains("-screenSettings") {
            _selection = State(initialValue: 2)
        } else {
            _selection = State(initialValue: 0)
        }
    }

    var body: some View {
        TabView(selection: $selection) {
            NavigationStack { ExploreView() }
                .tabItem { Label("Explore", systemImage: "map") }
                .tag(0)

            NavigationStack { SavedView() }
                .tabItem { Label("Saved", systemImage: "heart") }
                .tag(1)

            NavigationStack { SettingsView() }
                .tabItem { Label("Settings", systemImage: "gearshape") }
                .tag(2)
        }
    }
}

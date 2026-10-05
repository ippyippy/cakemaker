import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            NavigationStack { ExploreView() }
                .tabItem { Label("Explore", systemImage: "map") }

            NavigationStack { SavedView() }
                .tabItem { Label("Saved", systemImage: "heart") }

            NavigationStack { SettingsView() }
                .tabItem { Label("Settings", systemImage: "gearshape") }
        }
    }
}

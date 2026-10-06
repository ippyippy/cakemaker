import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var model: AppModel
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false
    @State private var selection: Int
    private let launchMode: LaunchMode
    private let skipOnboarding: Bool

    private enum LaunchMode {
        case tabs
        case onboarding
        case drive
    }

    init() {
        let args = ProcessInfo.processInfo.arguments
        skipOnboarding = args.contains("-skipOnboarding")

        if args.contains("-screenOnboarding") {
            launchMode = .onboarding
            _selection = State(initialValue: 0)
        } else if args.contains("-screenDrive") {
            launchMode = .drive
            _selection = State(initialValue: 0)
        } else {
            launchMode = .tabs
            if args.contains("-screenSaved") {
                _selection = State(initialValue: 1)
            } else if args.contains("-screenAlerts") {
                _selection = State(initialValue: 2)
            } else if args.contains("-screenSettings") || args.contains("-screenMore") {
                _selection = State(initialValue: 3)
            } else {
                _selection = State(initialValue: 0)
            }
        }
    }

    var body: some View {
        Group {
            switch launchMode {
            case .onboarding:
                OnboardingView(onDone: {})
            case .drive:
                DriveScreenshotHost()
            case .tabs:
                tabs
                    .fullScreenCover(
                        isPresented: Binding(
                            get: { !skipOnboarding && !hasCompletedOnboarding },
                            set: { newValue in
                                if !newValue { hasCompletedOnboarding = true }
                            }
                        )
                    ) {
                        OnboardingView {
                            hasCompletedOnboarding = true
                        }
                    }
            }
        }
    }

    private var tabs: some View {
        TabView(selection: $selection) {
            NavigationStack { ExploreView() }
                .tabItem { Label("Explore", systemImage: "magnifyingglass") }
                .tag(0)

            NavigationStack { SavedView(onExplore: { selection = 0 }) }
                .tabItem { Label("Saved", systemImage: "heart") }
                .tag(1)

            NavigationStack { AlertsView() }
                .tabItem { Label("Alerts", systemImage: "bell") }
                .tag(2)

            NavigationStack { SettingsView() }
                .tabItem { Label("More", systemImage: "line.3.horizontal") }
                .tag(3)
        }
        .tint(.fillMeGreen)
        .toolbarBackground(.visible, for: .tabBar)
        .toolbarBackground(Color.white, for: .tabBar)
    }
}

private struct DriveScreenshotHost: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        Group {
            if let best = model.best {
                DriveModeView(ranked: best)
            } else {
                ZStack {
                    Color.fillMeInk.ignoresSafeArea()
                    ProgressView("Loading current best stop…")
                        .tint(.fillMeGreen)
                        .foregroundStyle(.white)
                }
                .task {
                    await model.load()
                }
            }
        }
    }
}

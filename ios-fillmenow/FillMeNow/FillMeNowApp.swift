import SwiftUI

@main
struct FillMeNowApp: App {
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(model)
                .tint(.fillMeGreen)
        }
    }
}

extension Color {
    static let fillMeGreen = Color(red: 0.51, green: 0.93, blue: 0.22)
    static let fillMeInk = Color(red: 0.05, green: 0.08, blue: 0.06)
    static let fillMeSurface = Color(red: 0.95, green: 0.96, blue: 0.94)
}

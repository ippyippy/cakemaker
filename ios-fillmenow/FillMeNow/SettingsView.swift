import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        Form {
            Section("Vehicle") {
                Picker("Vehicle", selection: $model.vehiclePreset) {
                    ForEach(VehiclePreset.allCases) { preset in
                        Text(preset.title).tag(preset)
                    }
                }
                .onChange(of: model.vehiclePreset) { preset in
                    model.selectVehicle(preset)
                }

                HStack {
                    Text("Typical fill")
                    Spacer()
                    Text("\(Int(model.tankLitres)) L")
                        .foregroundStyle(.secondary)
                }

                Slider(value: $model.tankLitres, in: 20...1200, step: 5)
                    .onChange(of: model.tankLitres) { _ in
                        if model.vehiclePreset != .custom { model.vehiclePreset = .custom }
                        model.savePreferences()
                        model.rerank()
                    }

                HStack {
                    Text("Fuel economy")
                    Spacer()
                    Text(String(format: "%.1f L/100km", model.economyLPer100km))
                        .foregroundStyle(.secondary)
                }

                Slider(value: $model.economyLPer100km, in: 3...60, step: 0.5)
                    .onChange(of: model.economyLPer100km) { _ in
                        if model.vehiclePreset != .custom { model.vehiclePreset = .custom }
                        model.savePreferences()
                        model.rerank()
                    }
            }

            Section("About") {
                LabeledContent("Coverage", value: "NSW · WA · TAS")
                LabeledContent("Version", value: "1.0.0")

                Link(destination: URL(string: "https://fillmenow-au.vercel.app/privacy.html")!) {
                    Label("Privacy Policy", systemImage: "hand.raised")
                }

                Link(destination: URL(string: "https://fillmenow-au.vercel.app/terms.html")!) {
                    Label("Terms & Disclaimer", systemImage: "doc.text")
                }
            }

            Section {
                Text("Fuel prices can change after they are reported. Always confirm the displayed pump price before purchasing fuel.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
    }
}

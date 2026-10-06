import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("More")
                    .font(.system(size: 31, weight: .black, design: .rounded))
                    .tracking(-1.2)
                    .foregroundStyle(Color.fillMeInk)
                    .padding(.top, 10)

                DashMascotView(height: 150, cornerRadius: 22)

                settingsCard

                aboutCard

                Text("Fuel prices can change after they are reported. Always confirm the displayed pump price before purchasing fuel.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 4)
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 30)
        }
        .background(Color.white.ignoresSafeArea())
        .navigationBarHidden(true)
    }

    private var settingsCard: some View {
        VStack(spacing: 0) {
            Picker("Vehicle", selection: $model.vehiclePreset) {
                ForEach(VehiclePreset.allCases) { preset in
                    Text(preset.title).tag(preset)
                }
            }
            .onChange(of: model.vehiclePreset) { model.selectVehicle($0) }
            .padding(14)

            Divider()

            HStack {
                Label("Fuel Type", systemImage: "fuelpump.fill")
                Spacer()
                Text(model.fuel).foregroundStyle(.secondary)
            }
            .padding(14)

            Divider()

            HStack {
                Label("Search Radius", systemImage: "scope")
                Spacer()
                Text("\(Int(model.radiusKm)) km").foregroundStyle(.secondary)
            }
            .padding(14)

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Typical fill")
                    Spacer()
                    Text("\(Int(model.tankLitres)) L").foregroundStyle(.secondary)
                }
                Slider(value: $model.tankLitres, in: 20...1200, step: 5)
                    .onChange(of: model.tankLitres) { _ in
                        if model.vehiclePreset != .custom { model.vehiclePreset = .custom }
                        model.savePreferences()
                        model.rerank()
                    }
            }
            .padding(14)
        }
        .font(.subheadline.weight(.semibold))
        .background(Color.white)
        .overlay(RoundedRectangle(cornerRadius: 20).stroke(Color.black.opacity(0.07)))
        .clipShape(RoundedRectangle(cornerRadius: 20))
    }

    private var aboutCard: some View {
        VStack(spacing: 0) {
            HStack {
                Label("Coverage", systemImage: "map")
                Spacer()
                Text("NSW · WA · TAS").foregroundStyle(.secondary)
            }
            .padding(14)

            Divider()

            Link(destination: URL(string: "https://fillmenow-au.vercel.app/privacy.html")!) {
                HStack {
                    Label("Privacy Policy", systemImage: "hand.raised")
                    Spacer()
                    Image(systemName: "chevron.right")
                }
            }
            .padding(14)

            Divider()

            Link(destination: URL(string: "https://fillmenow-au.vercel.app/terms.html")!) {
                HStack {
                    Label("Terms & Disclaimer", systemImage: "doc.text")
                    Spacer()
                    Image(systemName: "chevron.right")
                }
            }
            .padding(14)
        }
        .font(.subheadline.weight(.semibold))
        .foregroundStyle(Color.fillMeInk)
        .background(Color.white)
        .overlay(RoundedRectangle(cornerRadius: 20).stroke(Color.black.opacity(0.07)))
        .clipShape(RoundedRectangle(cornerRadius: 20))
    }
}

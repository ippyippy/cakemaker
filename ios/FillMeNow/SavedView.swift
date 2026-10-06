import SwiftUI

struct SavedView: View {
    @EnvironmentObject private var model: AppModel
    let onExplore: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("Saved Stations")
                    .font(.system(size: 31, weight: .black, design: .rounded))
                    .tracking(-1.2)
                    .foregroundStyle(Color.fillMeInk)
                    .padding(.top, 10)

                if model.currentSavedStations.isEmpty {
                    emptyState
                } else {
                    ForEach(model.currentSavedStations) { station in
                        savedCard(station)
                    }

                    Button {
                        onExplore()
                    } label: {
                        Label("Explore Nearby Stations", systemImage: "magnifyingglass")
                            .font(.headline.weight(.black))
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.fillMeGreen)
                    .foregroundStyle(.white)
                    .controlSize(.large)
                }
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 24)
        }
        .background(Color.white.ignoresSafeArea())
        .navigationBarHidden(true)
    }

    private var emptyState: some View {
        VStack(spacing: 14) {
            ZStack(alignment: .bottom) {
                DashMascotView(height: 330, cornerRadius: 28)

                Image(systemName: "heart.fill")
                    .font(.system(size: 104, weight: .black))
                    .foregroundStyle(Color.fillMeGreen)
                    .shadow(color: .black.opacity(0.12), radius: 12, y: 6)
                    .offset(y: 16)
            }
            .padding(.bottom, 18)

            Text("No saved stations yet")
                .font(.system(size: 27, weight: .black, design: .rounded))
                .foregroundStyle(Color.fillMeInk)

            Text("Tap the heart on any station to save it here.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 20)

            VStack(alignment: .leading, spacing: 14) {
                benefit("heart.fill", "Save your go-to stations")
                benefit("tag.fill", "Keep track of great prices")
                benefit("clock.fill", "Quick access on the go")
            }
            .padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.fillMeGreen.opacity(0.10))
            .clipShape(RoundedRectangle(cornerRadius: 20))

            Button {
                onExplore()
            } label: {
                Text("Explore Nearby Stations")
                    .font(.headline.weight(.black))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.fillMeGreen)
            .foregroundStyle(.white)
            .controlSize(.large)
        }
    }

    private func benefit(_ icon: String, _ text: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundStyle(Color.fillMeGreen)
                .font(.title3.weight(.black))
                .frame(width: 24)
            Text(text)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Color.fillMeInk)
        }
    }

    private func savedCard(_ station: FuelStation) -> some View {
        let ranked = model.stations.first(where: { $0.station.id == station.id })
        return HStack(spacing: 12) {
            StationLogoView(station: station, size: 50)

            VStack(alignment: .leading, spacing: 4) {
                Text(station.station_name)
                    .font(.headline.weight(.black))
                    .foregroundStyle(Color.fillMeInk)
                Text(station.suburb ?? "")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                if let price = ranked?.station.price ?? station.price {
                    Text(String(format: "%.1f¢/L", price))
                        .font(.subheadline.weight(.black))
                        .foregroundStyle(Color.fillMeGreen)
                }
            }

            Spacer()

            Button {
                model.openInAppleMaps(station)
            } label: {
                Image(systemName: "location.fill")
                    .frame(width: 40, height: 40)
            }
            .buttonStyle(.borderedProminent)
            .tint(.fillMeGreen)
            .foregroundStyle(.white)

            Button {
                model.toggleSaved(station)
            } label: {
                Image(systemName: "heart.slash")
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding(14)
        .background(Color.white)
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.black.opacity(0.07)))
        .clipShape(RoundedRectangle(cornerRadius: 18))
    }
}

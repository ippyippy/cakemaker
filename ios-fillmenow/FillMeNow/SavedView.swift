import SwiftUI

struct SavedView: View {
    @EnvironmentObject private var model: AppModel
    @State private var selectedStation: RankedStation?

    var body: some View {
        Group {
            if model.currentSavedStations.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "heart")
                        .font(.system(size: 42, weight: .light))
                        .foregroundStyle(Color.fillMeGreen)

                    Text("No saved stations yet")
                        .font(.headline.weight(.black))

                    Text("Save the stations you use most from Explore.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.fillMeSurface)
            } else {
                List {
                    ForEach(model.currentSavedStations) { station in
                        let ranked = model.stations.first(where: { $0.station.id == station.id })
                        HStack(spacing: 12) {
                            StationLogoView(station: station, size: 44)

                            VStack(alignment: .leading, spacing: 3) {
                                Text(station.station_name)
                                    .font(.headline.weight(.bold))
                                Text(station.suburb ?? "")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                if let price = ranked?.station.price ?? station.price {
                                    Text(String(format: "%.1f¢/L", price))
                                        .font(.subheadline.weight(.black))
                                }
                            }

                            Spacer()

                            Button {
                                model.openInAppleMaps(station)
                            } label: {
                                Image(systemName: "location.fill")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.fillMeGreen)
                            .foregroundStyle(.black)
                        }
                        .swipeActions {
                            Button(role: .destructive) {
                                model.toggleSaved(station)
                            } label: {
                                Label("Remove", systemImage: "trash")
                            }
                        }
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("Saved Stations")
        .navigationBarTitleDisplayMode(.inline)
    }
}

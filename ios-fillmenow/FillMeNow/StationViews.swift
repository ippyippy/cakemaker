import SwiftUI

struct StationRow: View {
    let ranked: RankedStation
    let rank: Int?
    let onGo: () -> Void
    let onDetails: () -> Void

    var body: some View {
        Button(action: onDetails) {
            HStack(spacing: 11) {
                ZStack(alignment: .bottomTrailing) {
                    StationLogoView(station: ranked.station, size: 42)
                    if let rank {
                        Text("\(rank)")
                            .font(.system(size: 8, weight: .black))
                            .foregroundStyle(.white)
                            .frame(minWidth: 18, minHeight: 18)
                            .background(Color.fillMeInk)
                            .clipShape(Circle())
                            .overlay(Circle().stroke(.white, lineWidth: 2))
                            .offset(x: 4, y: 4)
                    }
                }

                VStack(alignment: .leading, spacing: 3) {
                    Text(ranked.station.station_name)
                        .font(.system(size: 15, weight: .bold))
                        .foregroundStyle(Color.fillMeInk)
                        .lineLimit(1)

                    HStack(spacing: 6) {
                        Text(String(format: "%.1f¢/L", ranked.station.price ?? 0))
                            .font(.system(size: 17, weight: .black))
                            .foregroundStyle(Color.fillMeInk)

                        Text(String(format: "%.1f km · ~%d min", ranked.distanceKm, ranked.etaMinutes))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    if ranked.saving > 0 {
                        Text("Save about \(ranked.saving, format: .currency(code: "AUD"))")
                            .font(.caption2.weight(.bold))
                            .foregroundStyle(.green)
                    }
                }

                Spacer(minLength: 4)

                Button("GO", action: onGo)
                    .font(.caption.weight(.black))
                    .buttonStyle(.borderedProminent)
                    .tint(.fillMeGreen)
                    .foregroundStyle(.black)
            }
            .padding(.vertical, 7)
        }
        .buttonStyle(.plain)
    }
}

struct StationDetailView: View {
    @EnvironmentObject private var model: AppModel
    let ranked: RankedStation
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    HStack(spacing: 12) {
                        StationLogoView(station: ranked.station, size: 58)
                        VStack(alignment: .leading, spacing: 4) {
                            Text(ranked.station.station_name)
                                .font(.title2.bold())
                            Text([ranked.station.address, ranked.station.suburb, ranked.station.postcode]
                                .compactMap { $0 }
                                .filter { !$0.isEmpty }
                                .joined(separator: " · "))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }

                    HStack(spacing: 10) {
                        MetricCard(title: "Price", value: String(format: "%.1f¢/L", ranked.station.price ?? 0))
                        MetricCard(title: "Distance", value: String(format: "%.1f km", ranked.distanceKm))
                    }

                    HStack(spacing: 10) {
                        MetricCard(title: "After travel", value: String(format: "%.1f¢/L", ranked.effectivePrice))
                        MetricCard(title: "Est. saving", value: ranked.saving > 0 ? ranked.saving.formatted(.currency(code: "AUD")) : "—")
                    }

                    Button {
                        model.openInAppleMaps(ranked.station)
                    } label: {
                        Label("Navigate with Apple Maps", systemImage: "location.fill")
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 6)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.fillMeGreen)
                    .foregroundStyle(.black)

                    Button {
                        model.toggleSaved(ranked.station)
                    } label: {
                        Label(model.isSaved(ranked.station) ? "Remove saved station" : "Save station",
                              systemImage: model.isSaved(ranked.station) ? "heart.slash" : "heart")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                }
                .padding()
            }
            .navigationTitle("Station")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

private struct MetricCard: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title.uppercased())
                .font(.caption2.weight(.bold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.headline.weight(.black))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color.fillMeSurface)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

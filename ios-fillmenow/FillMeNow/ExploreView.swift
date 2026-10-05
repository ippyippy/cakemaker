import SwiftUI
import CoreLocation

struct ExploreView: View {
    @EnvironmentObject private var model: AppModel
    @StateObject private var locationManager = LocationManager()
    @State private var selectedStation: RankedStation?
    @State private var showAll = false

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                header
                controls
                locationSearch

                if let error = locationManager.errorMessage ?? model.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 2)
                }

                mapCard

                if let best = model.best {
                    bestCard(best)
                }

                if !model.stations.isEmpty {
                    nearbySection
                }
            }
            .padding(14)
        }
        .background(Color.fillMeSurface.ignoresSafeArea())
        .navigationBarHidden(true)
        .task {
            if model.stations.isEmpty {
                await model.load()
            }
        }
        .onReceive(locationManager.$coordinate.compactMap { $0 }) { coordinate in
            Task {
                await model.useCoordinate(coordinate, name: "Current location")
            }
        }
        .sheet(item: $selectedStation) { station in
            StationDetailView(ranked: station)
                .environmentObject(model)
        }
        .sheet(isPresented: $showAll) {
            NavigationStack {
                NearbyListView(onSelect: { station in
                    showAll = false
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                        selectedStation = station
                    }
                })
                .environmentObject(model)
            }
        }
    }

    private var header: some View {
        HStack(spacing: 10) {
            Image(systemName: "drop.fill")
                .font(.title2.weight(.black))
                .foregroundStyle(Color.fillMeGreen)

            VStack(alignment: .leading, spacing: 0) {
                Text("FillMeNow")
                    .font(.title2.weight(.black))
                    .foregroundStyle(.white)
                Text("CHEAPER FUEL. SMARTER STOPS.")
                    .font(.system(size: 8, weight: .bold))
                    .foregroundStyle(.white.opacity(0.55))
            }

            Spacer()

            Text(model.selectedLocationName)
                .font(.caption2.weight(.bold))
                .foregroundStyle(.white)
                .lineLimit(1)
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
                .background(.white.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .padding(14)
        .background(Color.fillMeInk)
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private var controls: some View {
        VStack(spacing: 8) {
            HStack(spacing: 8) {
                Menu {
                    Picker("State", selection: $model.state) {
                        ForEach(FuelState.allCases) { state in
                            Text(state.name).tag(state)
                        }
                    }
                } label: {
                    ControlTile(title: "STATE", value: model.state.rawValue)
                }
                .onChange(of: model.state) { _ in
                    model.normalizeFuel()
                    model.savePreferences()
                    Task { await model.load() }
                }

                Menu {
                    Picker("Fuel", selection: $model.fuel) {
                        ForEach(model.state.fuels, id: \.self) { fuel in
                            Text(fuel).tag(fuel)
                        }
                    }
                } label: {
                    ControlTile(title: "FUEL", value: model.fuel)
                }
                .onChange(of: model.fuel) { _ in
                    model.savePreferences()
                    Task { await model.load() }
                }

                Menu {
                    Picker("Radius", selection: $model.radiusKm) {
                        ForEach([5.0, 10, 20, 30, 50, 100], id: \.self) { radius in
                            Text("\(Int(radius)) km").tag(radius)
                        }
                    }
                } label: {
                    ControlTile(title: "RADIUS", value: "\(Int(model.radiusKm)) km")
                }
                .onChange(of: model.radiusKm) { _ in
                    model.savePreferences()
                    Task { await model.load() }
                }
            }
        }
    }

    private var locationSearch: some View {
        HStack(spacing: 8) {
            TextField("Suburb or postcode", text: $model.searchText)
                .textInputAutocapitalization(.words)
                .submitLabel(.search)
                .onSubmit { Task { await model.searchPlace() } }
                .padding(11)
                .background(.white)
                .clipShape(RoundedRectangle(cornerRadius: 10))

            Button {
                Task { await model.searchPlace() }
            } label: {
                Image(systemName: "magnifyingglass")
                    .frame(width: 42, height: 42)
            }
            .buttonStyle(.borderedProminent)
            .tint(.fillMeInk)

            Button {
                locationManager.requestCurrentLocation()
            } label: {
                Image(systemName: "location.fill")
                    .frame(width: 42, height: 42)
            }
            .buttonStyle(.borderedProminent)
            .tint(.fillMeGreen)
            .foregroundStyle(.black)
        }
    }

    private var mapCard: some View {
        ZStack(alignment: .bottomLeading) {
            NativeStationMap(
                stations: model.stations,
                center: model.selectedCoordinate,
                radiusKm: model.radiusKm,
                onSelect: { selectedStation = $0 }
            )
            .frame(height: 350)
            .clipShape(RoundedRectangle(cornerRadius: 14))

            Text("\(model.stations.count) station\(model.stations.count == 1 ? "" : "s") in \(Int(model.radiusKm)) km")
                .font(.caption2.weight(.black))
                .foregroundStyle(.white)
                .padding(.horizontal, 10)
                .padding(.vertical, 7)
                .background(Color.fillMeInk.opacity(0.92))
                .clipShape(Capsule())
                .padding(10)

            if model.isLoading {
                ProgressView()
                    .tint(.fillMeGreen)
                    .padding(12)
                    .background(.ultraThinMaterial)
                    .clipShape(Circle())
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private func bestCard(_ best: RankedStation) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("BEST STOP")
                .font(.caption2.weight(.black))
                .foregroundStyle(Color.fillMeGreen)

            HStack(spacing: 12) {
                StationLogoView(station: best.station, size: 54)

                VStack(alignment: .leading, spacing: 3) {
                    Text(best.station.station_name)
                        .font(.headline.weight(.black))
                        .foregroundStyle(.white)
                    Text(String(format: "%.1f km · ~%d min", best.distanceKm, best.etaMinutes))
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.6))
                }

                Spacer()

                Text(String(format: "%.1f¢", best.station.price ?? 0))
                    .font(.title2.weight(.black))
                    .foregroundStyle(.white)
            }

            if best.saving > 0 {
                Text("Save about \(best.saving, format: .currency(code: "AUD")) on a \(Int(model.tankLitres)) L fill")
                    .font(.subheadline.weight(.bold))
                    .foregroundStyle(Color.fillMeGreen)
            }

            HStack(spacing: 8) {
                Button {
                    model.openInAppleMaps(best.station)
                } label: {
                    Label("GO", systemImage: "arrow.triangle.turn.up.right.diamond.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(.fillMeGreen)
                .foregroundStyle(.black)

                Button("Details") {
                    selectedStation = best
                }
                .frame(maxWidth: .infinity)
                .buttonStyle(.bordered)
                .tint(.white)
            }
        }
        .padding(16)
        .background(Color.fillMeInk)
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private var nearbySection: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Nearby Options")
                        .font(.headline.weight(.black))
                    Text("Ranked by estimated total trip cost")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button("View all \(model.stations.count)") { showAll = true }
                    .font(.caption.weight(.bold))
            }
            .padding(.bottom, 8)

            VStack(spacing: 0) {
                ForEach(Array(model.stations.prefix(8).enumerated()), id: \.element.id) { index, ranked in
                    StationRow(
                        ranked: ranked,
                        rank: index + 1,
                        onGo: { model.openInAppleMaps(ranked.station) },
                        onDetails: { selectedStation = ranked }
                    )
                    if index < min(model.stations.count, 8) - 1 {
                        Divider()
                    }
                }
            }
            .padding(.horizontal, 12)
            .background(.white)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
    }
}

private struct ControlTile: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title)
                .font(.system(size: 8, weight: .bold))
                .foregroundStyle(.secondary)
            HStack {
                Text(value)
                    .font(.caption.weight(.black))
                    .foregroundStyle(Color.fillMeInk)
                    .lineLimit(1)
                Spacer(minLength: 2)
                Image(systemName: "chevron.down")
                    .font(.system(size: 8, weight: .black))
                    .foregroundStyle(.secondary)
            }
        }
        .padding(10)
        .frame(maxWidth: .infinity, minHeight: 52)
        .background(.white)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

struct NearbyListView: View {
    @EnvironmentObject private var model: AppModel
    let onSelect: (RankedStation) -> Void

    var body: some View {
        List {
            ForEach(Array(model.stations.enumerated()), id: \.element.id) { index, ranked in
                StationRow(
                    ranked: ranked,
                    rank: index + 1,
                    onGo: { model.openInAppleMaps(ranked.station) },
                    onDetails: { onSelect(ranked) }
                )
            }
        }
        .listStyle(.plain)
        .navigationTitle("\(model.stations.count) Nearby Stations")
        .navigationBarTitleDisplayMode(.inline)
    }
}

import SwiftUI
import CoreLocation

struct ExploreView: View {
    @EnvironmentObject private var model: AppModel
    @StateObject private var locationManager = LocationManager()
    @State private var selectedStation: RankedStation?
    @State private var showAll = false
    @State private var showSearch = false
    @State private var driveStation: RankedStation?

    var body: some View {
        VStack(spacing: 0) {
            header

            ZStack(alignment: .top) {
                NativeStationMap(
                    stations: model.stations,
                    center: model.selectedCoordinate,
                    radiusKm: model.radiusKm,
                    onSelect: { selectedStation = $0 }
                )
                .ignoresSafeArea(edges: .horizontal)

                VStack(spacing: 10) {
                    if showSearch {
                        searchPanel
                            .transition(.move(edge: .top).combined(with: .opacity))
                    }

                    Spacer()

                    if let best = model.best {
                        bestCard(best)
                    } else if model.isLoading {
                        ProgressView("Finding nearby fuel…")
                            .padding(16)
                            .background(.ultraThinMaterial)
                            .clipShape(RoundedRectangle(cornerRadius: 18))
                            .padding(.horizontal, 14)
                            .padding(.bottom, 10)
                    } else {
                        emptyCard
                    }
                }
                .padding(.top, 10)
            }
        }
        .background(Color.white)
        .navigationBarHidden(true)
        .task {
            if model.stations.isEmpty {
                await model.load()
            }
        }
        .onReceive(locationManager.$coordinate.compactMap { $0 }) { coordinate in
            Task { await model.useCoordinate(coordinate, name: "Current location") }
        }
        .sheet(item: $selectedStation) { station in
            StationDetailView(ranked: station)
                .environmentObject(model)
                .presentationDetents([.medium, .large])
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
        .fullScreenCover(item: $driveStation) { station in
            DriveModeView(ranked: station)
                .environmentObject(model)
        }
    }

    private var header: some View {
        HStack(spacing: 10) {
            ZStack {
                Image(systemName: "drop.fill")
                    .font(.system(size: 31, weight: .black))
                    .foregroundStyle(Color.fillMeInk)
                Circle()
                    .fill(Color.fillMeGreen)
                    .frame(width: 12, height: 12)
                    .offset(x: 7, y: 6)
            }

            HStack(spacing: 0) {
                Text("Fill")
                    .foregroundStyle(Color.fillMeInk)
                Text("MeNow")
                    .foregroundStyle(Color.fillMeGreen)
            }
            .font(.system(size: 29, weight: .black, design: .rounded))
            .tracking(-1.4)

            Spacer()

            Button {
                withAnimation(.easeInOut(duration: 0.18)) { showSearch.toggle() }
            } label: {
                Image(systemName: showSearch ? "xmark" : "magnifyingglass")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundStyle(Color.fillMeInk)
                    .frame(width: 48, height: 48)
                    .background(Color.white)
                    .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.black.opacity(0.08)))
                    .clipShape(RoundedRectangle(cornerRadius: 15))
            }
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 10)
        .background(Color.white)
        .overlay(alignment: .bottom) { Divider().opacity(0.35) }
    }

    private var searchPanel: some View {
        VStack(spacing: 9) {
            HStack(spacing: 8) {
                TextField("Suburb or postcode", text: $model.searchText)
                    .textInputAutocapitalization(.words)
                    .submitLabel(.search)
                    .onSubmit { Task { await model.searchPlace() } }
                    .padding(.horizontal, 12)
                    .frame(height: 46)
                    .background(Color.white)
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.black.opacity(0.08)))
                    .clipShape(RoundedRectangle(cornerRadius: 14))

                Button {
                    Task { await model.searchPlace() }
                } label: {
                    Image(systemName: "magnifyingglass")
                        .frame(width: 46, height: 46)
                }
                .buttonStyle(.borderedProminent)
                .tint(.fillMeInk)

                Button {
                    locationManager.requestCurrentLocation()
                } label: {
                    Image(systemName: "location.fill")
                        .frame(width: 46, height: 46)
                }
                .buttonStyle(.borderedProminent)
                .tint(.fillMeGreen)
                .foregroundStyle(.white)
            }

            HStack(spacing: 8) {
                Menu {
                    Picker("Fuel", selection: $model.fuel) {
                        ForEach(model.state.fuels, id: \.self) { Text($0).tag($0) }
                    }
                } label: {
                    SearchChip(title: "Fuel", value: model.fuel)
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
                    SearchChip(title: "Radius", value: "\(Int(model.radiusKm)) km")
                }
                .onChange(of: model.radiusKm) { _ in
                    model.savePreferences()
                    Task { await model.load() }
                }

                Menu {
                    Picker("State", selection: $model.state) {
                        ForEach(FuelState.allCases) { Text($0.name).tag($0) }
                    }
                } label: {
                    SearchChip(title: "State", value: model.state.rawValue)
                }
                .onChange(of: model.state) { _ in
                    model.normalizeFuel()
                    model.savePreferences()
                    Task { await model.load() }
                }
            }

            if let error = locationManager.errorMessage ?? model.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(12)
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .padding(.horizontal, 12)
    }

    private func bestCard(_ best: RankedStation) -> some View {
        VStack(spacing: 0) {
            HStack(alignment: .top, spacing: 10) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("BEST STOP")
                        .font(.system(size: 12, weight: .black))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(Color.fillMeGreen)
                        .clipShape(RoundedRectangle(cornerRadius: 9))

                    HStack(spacing: 9) {
                        StationLogoView(station: best.station, size: 45)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(best.station.station_name)
                                .font(.system(size: 21, weight: .black))
                                .foregroundStyle(Color.fillMeInk)
                                .lineLimit(1)
                            Text(String(format: "%.1f km · ~%d min", best.distanceKm, best.etaMinutes))
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                Spacer()

                DashMascotView(height: 102, cornerRadius: 18)
                    .frame(width: 126)
            }

            HStack(alignment: .firstTextBaseline) {
                Text(String(format: "%.1f", best.station.price ?? 0))
                    .font(.system(size: 48, weight: .black, design: .rounded))
                    .tracking(-2.5)
                    .foregroundStyle(Color.fillMeInk)
                Text("¢/L")
                    .font(.headline.weight(.bold))
                    .foregroundStyle(.secondary)

                Spacer()

                if best.saving > 0 {
                    VStack(alignment: .trailing, spacing: 1) {
                        Text("Save about")
                            .font(.caption2.weight(.bold))
                            .foregroundStyle(.secondary)
                        Text(best.saving, format: .currency(code: "AUD"))
                            .font(.title3.weight(.black))
                            .foregroundStyle(Color.fillMeGreen)
                    }
                }
            }
            .padding(.top, 2)

            HStack(spacing: 8) {
                Button {
                    selectedStation = best
                } label: {
                    HStack {
                        Text("View Station")
                        Spacer()
                        Image(systemName: "chevron.right")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(.fillMeGreen)
                .foregroundStyle(.white)
                .controlSize(.large)

                Button {
                    driveStation = best
                } label: {
                    Image(systemName: "car.fill")
                        .frame(width: 48, height: 48)
                }
                .buttonStyle(.borderedProminent)
                .tint(.fillMeInk)
            }
            .font(.headline.weight(.black))

            Button("View all nearby options") { showAll = true }
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.fillMeInk)
                .padding(.top, 10)
        }
        .padding(16)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
        .shadow(color: .black.opacity(0.16), radius: 18, y: -2)
        .padding(.horizontal, 10)
        .padding(.bottom, 10)
    }

    private var emptyCard: some View {
        VStack(spacing: 7) {
            Text("Find cheaper fuel nearby")
                .font(.headline.weight(.black))
            Text("Use search or your location to compare nearby stations.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            Button("Choose location") { showSearch = true }
                .buttonStyle(.borderedProminent)
                .tint(.fillMeGreen)
        }
        .padding(18)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 22))
        .shadow(color: .black.opacity(0.12), radius: 14, y: 2)
        .padding(12)
    }
}

private struct SearchChip: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(title.uppercased())
                .font(.system(size: 7, weight: .bold))
                .foregroundStyle(.secondary)
            HStack(spacing: 4) {
                Text(value)
                    .font(.caption.weight(.black))
                    .lineLimit(1)
                Image(systemName: "chevron.down")
                    .font(.system(size: 7, weight: .black))
            }
        }
        .foregroundStyle(Color.fillMeInk)
        .padding(.horizontal, 10)
        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
        .background(Color.white)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.black.opacity(0.08)))
        .clipShape(RoundedRectangle(cornerRadius: 12))
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

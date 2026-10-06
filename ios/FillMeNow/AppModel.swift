import Foundation
import CoreLocation
import MapKit

@MainActor
final class AppModel: ObservableObject {
    private let backend = URL(string: "https://psytztnkeeymavzmpomv.supabase.co/functions/v1/fueldrop")!

    @Published var state: FuelState
    @Published var fuel: String
    @Published var radiusKm: Double
    @Published var tankLitres: Double
    @Published var economyLPer100km: Double
    @Published var vehiclePreset: VehiclePreset
    @Published var selectedCoordinate: CLLocationCoordinate2D
    @Published var selectedLocationName: String
    @Published var stations: [RankedStation] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var searchText = ""
    @Published var savedStations: [FuelStation]

    init() {
        let defaults = UserDefaults.standard

        state = FuelState(rawValue: defaults.string(forKey: "state") ?? "NSW") ?? .NSW
        fuel = defaults.string(forKey: "fuel") ?? "Diesel"
        radiusKm = defaults.object(forKey: "radiusKm") as? Double ?? 20
        tankLitres = defaults.object(forKey: "tankLitres") as? Double ?? 65
        economyLPer100km = defaults.object(forKey: "economyLPer100km") as? Double ?? 9
        vehiclePreset = VehiclePreset(rawValue: defaults.string(forKey: "vehiclePreset") ?? "car") ?? .car

        let lat = defaults.object(forKey: "selectedLat") as? Double ?? -33.8688
        let lng = defaults.object(forKey: "selectedLng") as? Double ?? 151.2093
        selectedCoordinate = .init(latitude: lat, longitude: lng)
        selectedLocationName = defaults.string(forKey: "selectedLocationName") ?? "Sydney NSW"

        if let data = defaults.data(forKey: "savedStations"),
           let decoded = try? JSONDecoder().decode([FuelStation].self, from: data) {
            savedStations = decoded
        } else {
            savedStations = []
        }

        normalizeFuel()
    }

    var best: RankedStation? { stations.first }

    var currentSavedStations: [FuelStation] {
        savedStations.map { saved in
            stations.first(where: { $0.station.id == saved.id })?.station ?? saved
        }
    }

    func normalizeFuel() {
        if !state.fuels.contains(fuel) {
            fuel = state.fuels.first ?? "Diesel"
        }
    }

    func savePreferences() {
        let d = UserDefaults.standard
        d.set(state.rawValue, forKey: "state")
        d.set(fuel, forKey: "fuel")
        d.set(radiusKm, forKey: "radiusKm")
        d.set(tankLitres, forKey: "tankLitres")
        d.set(economyLPer100km, forKey: "economyLPer100km")
        d.set(vehiclePreset.rawValue, forKey: "vehiclePreset")
        d.set(selectedCoordinate.latitude, forKey: "selectedLat")
        d.set(selectedCoordinate.longitude, forKey: "selectedLng")
        d.set(selectedLocationName, forKey: "selectedLocationName")
    }

    func selectVehicle(_ preset: VehiclePreset) {
        vehiclePreset = preset
        if let values = preset.defaults {
            tankLitres = values.tank
            economyLPer100km = values.economy
        }
        savePreferences()
        rerank()
    }

    func useCoordinate(_ coordinate: CLLocationCoordinate2D, name: String) async {
        selectedCoordinate = coordinate
        selectedLocationName = name
        savePreferences()
        await load()
    }

    func searchPlace() async {
        let q = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = "\(q), \(state.name), Australia"
        request.resultTypes = [.address, .pointOfInterest]

        do {
            let result = try await MKLocalSearch(request: request).start()
            guard let item = result.mapItems.first else {
                errorMessage = "No matching suburb or postcode found."
                return
            }
            let coordinate = item.placemark.coordinate
            selectedCoordinate = coordinate
            selectedLocationName = [
                item.placemark.locality,
                item.placemark.administrativeArea
            ].compactMap { $0 }.joined(separator: " ")
            if selectedLocationName.isEmpty { selectedLocationName = q }
            searchText = ""
            savePreferences()
            await load()
        } catch {
            errorMessage = "Location search failed. Try another suburb or postcode."
        }
    }

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        var components = URLComponents(url: backend, resolvingAgainstBaseURL: false)!
        components.queryItems = [
            .init(name: "api", value: "prices"),
            .init(name: "state", value: state.rawValue),
            .init(name: "fuel", value: fuel),
            .init(name: "lat", value: String(selectedCoordinate.latitude)),
            .init(name: "lng", value: String(selectedCoordinate.longitude)),
            .init(name: "radius", value: String(Int(radiusKm.rounded())))
        ]

        guard let url = components.url else {
            errorMessage = "Could not build the fuel-price request."
            return
        }

        do {
            var request = URLRequest(url: url)
            request.cachePolicy = .reloadIgnoringLocalCacheData
            request.timeoutInterval = 20

            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
                errorMessage = "Fuel prices could not be loaded."
                return
            }

            let decoded = try JSONDecoder().decode(PriceResponse.self, from: data)
            rank(decoded.rows)
        } catch {
            stations = []
            errorMessage = "Fuel prices could not be loaded. Check your connection and try again."
        }
    }

    func rerank() {
        rank(stations.map(\.station))
    }

    private func rank(_ rows: [FuelStation]) {
        let origin = CLLocation(latitude: selectedCoordinate.latitude, longitude: selectedCoordinate.longitude)

        var eligible: [(FuelStation, Double)] = rows.compactMap { station in
            guard let price = station.price, price > 0 else { return nil }
            let here = CLLocation(latitude: station.latitude, longitude: station.longitude)
            let km = origin.distance(from: here) / 1000
            guard km <= radiusKm else { return nil }
            return (station, km)
        }

        guard !eligible.isEmpty else {
            stations = []
            return
        }

        let prices = eligible.compactMap { $0.0.price }.sorted()
        let median = prices[prices.count / 2]

        let ranked = eligible.compactMap { station, distance -> RankedStation? in
            guard let price = station.price else { return nil }
            let roadKm = distance * 1.18
            let travelCost = roadKm * 2 * economyLPer100km / 100 * (price / 100)
            let effective = ((tankLitres * price / 100) + travelCost) / tankLitres * 100
            let saving = tankLitres * (median - price) / 100 - travelCost
            return RankedStation(
                station: station,
                distanceKm: distance,
                roadKm: roadKm,
                etaMinutes: max(2, Int((roadKm / 45 * 60).rounded())),
                effectivePrice: effective,
                saving: saving
            )
        }
        .sorted {
            if abs($0.effectivePrice - $1.effectivePrice) > 0.001 {
                return $0.effectivePrice < $1.effectivePrice
            }
            return ($0.station.price ?? .greatestFiniteMagnitude) < ($1.station.price ?? .greatestFiniteMagnitude)
        }

        stations = ranked
        eligible.removeAll(keepingCapacity: false)
    }

    func isSaved(_ station: FuelStation) -> Bool {
        savedStations.contains(where: { $0.id == station.id })
    }

    func toggleSaved(_ station: FuelStation) {
        if let index = savedStations.firstIndex(where: { $0.id == station.id }) {
            savedStations.remove(at: index)
        } else {
            savedStations.append(station)
        }

        if let data = try? JSONEncoder().encode(savedStations) {
            UserDefaults.standard.set(data, forKey: "savedStations")
        }
    }

    func openInAppleMaps(_ station: FuelStation) {
        let placemark = MKPlacemark(coordinate: station.coordinate)
        let item = MKMapItem(placemark: placemark)
        item.name = station.station_name
        item.openInMaps(launchOptions: [
            MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving
        ])
    }
}

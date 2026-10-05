import SwiftUI
import MapKit
import UIKit

struct NativeStationMap: UIViewRepresentable {
    let stations: [RankedStation]
    let center: CLLocationCoordinate2D
    let radiusKm: Double
    let onSelect: (RankedStation) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(onSelect: onSelect)
    }

    func makeUIView(context: Context) -> MKMapView {
        let map = MKMapView(frame: .zero)
        map.delegate = context.coordinator
        map.showsCompass = true
        map.showsScale = false
        map.showsUserLocation = true
        map.pointOfInterestFilter = .excludingAll
        return map
    }

    func updateUIView(_ map: MKMapView, context: Context) {
        context.coordinator.onSelect = onSelect

        let stationIDs = Set(stations.map(\.id))
        let existing = map.annotations.compactMap { $0 as? StationAnnotation }
        let existingIDs = Set(existing.map { $0.ranked.id })

        if stationIDs != existingIDs {
            map.removeAnnotations(existing)
            map.addAnnotations(stations.map(StationAnnotation.init))
        }

        let signature = "\(stations.count)-\(center.latitude)-\(center.longitude)-\(radiusKm)"
        if context.coordinator.lastRegionSignature != signature {
            context.coordinator.lastRegionSignature = signature
            let spanDegrees = max(0.02, radiusKm / 48)
            map.setRegion(
                MKCoordinateRegion(
                    center: center,
                    span: .init(latitudeDelta: spanDegrees, longitudeDelta: spanDegrees)
                ),
                animated: false
            )
        }
    }

    final class StationAnnotation: NSObject, MKAnnotation {
        let ranked: RankedStation
        let coordinate: CLLocationCoordinate2D
        var title: String? { ranked.station.station_name }

        init(_ ranked: RankedStation) {
            self.ranked = ranked
            coordinate = ranked.station.coordinate
        }
    }

    final class Coordinator: NSObject, MKMapViewDelegate {
        var onSelect: (RankedStation) -> Void
        var lastRegionSignature = ""

        init(onSelect: @escaping (RankedStation) -> Void) {
            self.onSelect = onSelect
        }

        func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
            if annotation is MKUserLocation { return nil }

            if let cluster = annotation as? MKClusterAnnotation {
                let id = "FuelCluster"
                let view = (mapView.dequeueReusableAnnotationView(withIdentifier: id) as? MKMarkerAnnotationView)
                    ?? MKMarkerAnnotationView(annotation: cluster, reuseIdentifier: id)
                view.annotation = cluster
                view.markerTintColor = UIColor(red: 0.51, green: 0.93, blue: 0.22, alpha: 1)
                view.glyphTintColor = .black
                view.glyphText = String(cluster.memberAnnotations.count)
                view.titleVisibility = .hidden
                view.subtitleVisibility = .hidden
                view.displayPriority = .defaultHigh
                return view
            }

            guard let stationAnnotation = annotation as? StationAnnotation else { return nil }
            let id = "FuelStation"
            let view = (mapView.dequeueReusableAnnotationView(withIdentifier: id) as? FuelAnnotationView)
                ?? FuelAnnotationView(annotation: stationAnnotation, reuseIdentifier: id)
            view.annotation = stationAnnotation
            view.configure(stationAnnotation.ranked)
            return view
        }

        func mapView(_ mapView: MKMapView, didSelect view: MKAnnotationView) {
            guard let station = view.annotation as? StationAnnotation else { return }
            onSelect(station.ranked)
            mapView.deselectAnnotation(station, animated: false)
        }
    }
}

final class FuelAnnotationView: MKAnnotationView {
    private let logoView = UIImageView()
    private let fallbackLabel = UILabel()
    private let priceLabel = UILabel()
    private var representedID: String?

    override init(annotation: MKAnnotation?, reuseIdentifier: String?) {
        super.init(annotation: annotation, reuseIdentifier: reuseIdentifier)

        frame = CGRect(x: 0, y: 0, width: 92, height: 44)
        centerOffset = CGPoint(x: 0, y: -22)
        clusteringIdentifier = "fuel-station"
        collisionMode = .rectangle
        displayPriority = .defaultHigh

        backgroundColor = .white
        layer.cornerRadius = 8
        layer.borderWidth = 2
        layer.borderColor = UIColor.black.withAlphaComponent(0.8).cgColor
        layer.shadowColor = UIColor.black.cgColor
        layer.shadowOpacity = 0.18
        layer.shadowRadius = 5
        layer.shadowOffset = CGSize(width: 0, height: 3)

        logoView.contentMode = .scaleAspectFit
        logoView.layer.cornerRadius = 5
        logoView.clipsToBounds = true
        logoView.translatesAutoresizingMaskIntoConstraints = false

        fallbackLabel.font = .systemFont(ofSize: 7, weight: .black)
        fallbackLabel.textAlignment = .center
        fallbackLabel.adjustsFontSizeToFitWidth = true
        fallbackLabel.minimumScaleFactor = 0.5
        fallbackLabel.translatesAutoresizingMaskIntoConstraints = false

        priceLabel.font = .systemFont(ofSize: 13, weight: .black)
        priceLabel.textColor = .black
        priceLabel.translatesAutoresizingMaskIntoConstraints = false

        addSubview(logoView)
        addSubview(fallbackLabel)
        addSubview(priceLabel)

        NSLayoutConstraint.activate([
            logoView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 5),
            logoView.centerYAnchor.constraint(equalTo: centerYAnchor),
            logoView.widthAnchor.constraint(equalToConstant: 30),
            logoView.heightAnchor.constraint(equalToConstant: 30),

            fallbackLabel.leadingAnchor.constraint(equalTo: logoView.leadingAnchor, constant: 2),
            fallbackLabel.trailingAnchor.constraint(equalTo: logoView.trailingAnchor, constant: -2),
            fallbackLabel.centerYAnchor.constraint(equalTo: logoView.centerYAnchor),

            priceLabel.leadingAnchor.constraint(equalTo: logoView.trailingAnchor, constant: 6),
            priceLabel.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -4),
            priceLabel.centerYAnchor.constraint(equalTo: centerYAnchor)
        ])
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func prepareForReuse() {
        super.prepareForReuse()
        representedID = nil
        logoView.image = nil
        fallbackLabel.text = nil
    }

    func configure(_ ranked: RankedStation) {
        let station = ranked.station
        representedID = station.id
        priceLabel.text = String(format: "%.1f¢", station.price ?? 0)
        fallbackLabel.text = BrandLogo.label(brand: station.brand, name: station.station_name)
        logoView.image = nil

        guard let url = BrandLogo.url(brand: station.brand, name: station.station_name) else { return }
        let expectedID = station.id

        URLSession.shared.dataTask(with: url) { [weak self] data, _, _ in
            guard let data, let image = UIImage(data: data) else { return }
            DispatchQueue.main.async {
                guard self?.representedID == expectedID else { return }
                self?.logoView.image = image
                self?.fallbackLabel.text = nil
            }
        }.resume()
    }
}

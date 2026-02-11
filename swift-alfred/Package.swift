// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Alfred",
    platforms: [.macOS(.v13)],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "Alfred",
            swiftSettings: [.enableExperimentalFeature("StrictConcurrency")]
        )
    ]
)

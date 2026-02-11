import SwiftUI
import AppKit

@main
struct AlfredApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}

@MainActor
class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var popover: NSPopover!
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusItem.button {
            button.title = "\u{1F935}\u{200D}\u{2642}\u{FE0F}"
            button.toolTip = "Alfred"
            button.action = #selector(togglePopover)
            button.target = self
        }
        
        popover = NSPopover()
        popover.contentSize = NSSize(width: 340, height: 520)
        popover.behavior = .applicationDefined  // Pinned: doesn't dismiss on click outside
        popover.contentViewController = NSHostingController(
            rootView: AlfredView(dismissAction: { [weak self] in
                self?.popover.performClose(nil)
            })
            .preferredColorScheme(.dark)
        )
    }
    
    @objc func togglePopover() {
        if let button = statusItem.button {
            if popover.isShown {
                popover.performClose(nil)
            } else {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
                // Bring to front
                NSApplication.shared.activate(ignoringOtherApps: true)
            }
        }
    }
}

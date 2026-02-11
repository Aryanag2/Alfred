import SwiftUI
import UniformTypeIdentifiers

/// Thread-safe array for concurrent drop callbacks.
final class LockedArray: @unchecked Sendable {
    private var storage: [String] = []
    private let lock = NSLock()
    func append(_ value: String) {
        lock.lock(); defer { lock.unlock() }
        storage.append(value)
    }
    var values: [String] {
        lock.lock(); defer { lock.unlock() }
        return storage
    }
}

// MARK: - Main View

struct AlfredView: View {
    var dismissAction: (() -> Void)? = nil
    
    @State private var mode: Mode = .convert
    @State private var paths: [String] = []
    @State private var targetFormat: String = ""
    @State private var customCommand: String = ""
    @State private var organizeInstructions: String = ""
    @State private var logs: [String] = []
    @State private var isProcessing: Bool = false
    @State private var showFilePicker: Bool = false
    @State private var activeProcess: Process? = nil
    @State private var isDropTargeted: Bool = false
    @State private var hasPlan: Bool = false
    @State private var missingTool: String? = nil
    
    enum Mode: String, CaseIterable {
        case convert = "Convert"
        case organize = "Organize"
        case summarize = "Summarize"
        case rename = "Rename"
        case command = "Command"
        
        var icon: String {
            switch self {
            case .convert: return "arrow.triangle.2.circlepath"
            case .organize: return "folder.badge.gearshape"
            case .summarize: return "doc.text.magnifyingglass"
            case .rename: return "pencil.line"
            case .command: return "terminal"
            }
        }
        
        var hint: String {
            switch self {
            case .convert: return "Select a file and target format"
            case .organize: return "Select a folder to organize"
            case .summarize: return "Drop one or more files for batch summary"
            case .rename: return "Drop multiple files for batch rename"
            case .command: return "Describe what Alfred should do"
            }
        }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            headerBar
            Divider().opacity(0.3)
            
            if let tool = missingTool {
                installPrompt(tool)
            } else {
                modeSelector
                Divider().opacity(0.3)
                
                ScrollView {
                    VStack(spacing: 12) {
                        if mode != .command || !paths.isEmpty { fileInputSection }
                        modeSpecificInputs
                        actionButtons
                    }
                    .padding(.horizontal, 14)
                    .padding(.top, 10)
                }
                .frame(maxHeight: mode == .command && paths.isEmpty ? 100 : 180)
            }
            
            logSection
        }
        .frame(width: 340, height: 520)
        .fileImporter(
            isPresented: $showFilePicker,
            allowedContentTypes: allowedContentTypes,
            allowsMultipleSelection: mode == .summarize || mode == .rename
        ) { result in
            switch result {
            case .success(let urls):
                paths = urls.map { $0.path }
            case .failure(let error):
                logs.append("[ERR] \(error.localizedDescription)")
            }
        }
    }
    
    // MARK: - Header
    
    private var headerBar: some View {
        HStack {
            Text("Alfred")
                .font(.system(size: 15, weight: .bold, design: .rounded))
            Spacer()
            if isProcessing {
                ProgressView()
                    .controlSize(.small)
                    .scaleEffect(0.8)
            }
            Button(action: { dismissAction?() }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 14))
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
            .help("Close")
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
    }
    
    private func installPrompt(_ tool: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "wrench.and.screwdriver.fill")
                .font(.system(size: 32))
                .foregroundColor(.yellow)
            
            Text("Missing Tool: \(tool)")
                .font(.headline)
            
            Text("This action requires \(tool). Would you like to download and install it now?")
                .font(.caption)
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)
                .padding(.horizontal)
            
            HStack {
                Button("Cancel") {
                    missingTool = nil
                    logs.append("[WARN] Installation cancelled.")
                }
                .buttonStyle(.plain)
                .foregroundColor(.secondary)
                
                Button("Install \(tool)") {
                    installTool(tool)
                }
                .buttonStyle(.borderedProminent)
                .tint(.blue)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(NSColor.windowBackgroundColor))
    }
    
    // MARK: - Mode Selector
    
    private var modeSelector: some View {
        HStack(spacing: 4) {
            ForEach(Mode.allCases, id: \.self) { m in
                Button {
                    withAnimation(.easeInOut(duration: 0.15)) {
                        mode = m
                        paths = []
                        logs.removeAll()
                        hasPlan = false
                        organizeInstructions = ""
                        missingTool = nil
                    }
                } label: {
                    VStack(spacing: 3) {
                        Image(systemName: m.icon)
                            .font(.system(size: 12))
                        Text(m.rawValue)
                            .font(.system(size: 9, weight: .medium))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 6)
                    .background(mode == m ? Color.blue.opacity(0.25) : Color.clear)
                    .foregroundColor(mode == m ? .blue : .secondary)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
    }
    
    // MARK: - File Input
    
    private var fileInputSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(mode.hint)
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
                Spacer()
                if !paths.isEmpty {
                    Button {
                        paths = []
                        hasPlan = false
                        logs.removeAll()
                    } label: {
                        Image(systemName: "xmark.circle")
                            .font(.system(size: 10))
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.secondary)
                }
                Button("Browse") { showFilePicker = true }
                    .font(.system(size: 10))
                    .controlSize(.small)
            }
            
            if paths.isEmpty {
                ZStack {
                    RoundedRectangle(cornerRadius: 6)
                        .strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [5, 3]))
                        .foregroundColor(isDropTargeted ? .blue : .secondary.opacity(0.25))
                    VStack(spacing: 3) {
                        Image(systemName: "arrow.down.doc")
                            .font(.system(size: 14))
                            .foregroundColor(isDropTargeted ? .blue : .secondary.opacity(0.5))
                        Text("Drop here")
                            .font(.system(size: 10))
                            .foregroundColor(.secondary.opacity(0.6))
                    }
                }
                .frame(height: 48)
                .background(isDropTargeted ? Color.blue.opacity(0.05) : Color.clear)
                .cornerRadius(6)
                .onDrop(of: [.fileURL], isTargeted: $isDropTargeted) { providers in
                    handleDrop(providers: providers)
                    return true
                }
            } else {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(paths.prefix(4), id: \.self) { path in
                        HStack(spacing: 4) {
                            Image(systemName: iconForPath(path))
                                .font(.system(size: 8))
                                .foregroundColor(.secondary)
                            Text((path as NSString).lastPathComponent)
                                .font(.system(size: 10, design: .monospaced))
                                .lineLimit(1)
                                .truncationMode(.middle)
                        }
                    }
                    if paths.count > 4 {
                        Text("+ \(paths.count - 4) more")
                            .font(.system(size: 9))
                            .foregroundColor(.secondary)
                    }
                }
                .padding(6)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white.opacity(0.04))
                .cornerRadius(4)
                .onDrop(of: [.fileURL], isTargeted: $isDropTargeted) { providers in
                    handleDrop(providers: providers)
                    return true
                }
            }
        }
    }
    
    // MARK: - Mode-Specific Inputs
    
    @ViewBuilder
    private var modeSpecificInputs: some View {
        switch mode {
        case .convert:
            TextField("Target format (e.g. pdf, mp3, json)", text: $targetFormat)
                .textFieldStyle(.roundedBorder)
                .font(.system(size: 11))
        case .organize:
            VStack(alignment: .leading, spacing: 4) {
                Text("Instructions (optional)")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
                TextField("e.g. put screenshots in Screenshots...", text: $organizeInstructions, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(size: 11))
                    .lineLimit(2...3)
            }
        case .command:
            TextEditor(text: $customCommand)
                .font(.system(size: 11, design: .monospaced))
                .frame(height: 50)
                .overlay(RoundedRectangle(cornerRadius: 4).stroke(Color.secondary.opacity(0.2)))
                .overlay(
                    Group {
                        if customCommand.isEmpty {
                            Text("e.g. merge these two PDFs...")
                                .font(.system(size: 11))
                                .foregroundColor(.secondary.opacity(0.5))
                                .padding(.leading, 5)
                                .padding(.top, 8)
                                .allowsHitTesting(false)
                        }
                    },
                    alignment: .topLeading
                )
        default:
            EmptyView()
        }
    }
    
    // MARK: - Action Buttons
    
    private var actionButtons: some View {
        HStack(spacing: 8) {
            if hasPlan {
                Button {
                    performAction(confirmed: true)
                } label: {
                    Text("Confirm")
                        .font(.system(size: 12, weight: .semibold))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 7)
                }
                .buttonStyle(.borderedProminent)
                .tint(.green)
                .disabled(isProcessing)
            } else {
                Button {
                    performAction(confirmed: false)
                } label: {
                    Text(isProcessing ? "Working..." : actionLabel)
                        .font(.system(size: 12, weight: .semibold))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 7)
                }
                .buttonStyle(.borderedProminent)
                .tint(.blue)
                .disabled(isProcessing || !isReady)
            }
            
            if isProcessing {
                Button { cancelAction() } label: {
                    Image(systemName: "stop.circle.fill")
                        .font(.system(size: 16))
                }
                .buttonStyle(.plain)
                .foregroundColor(.red)
            }
        }
    }
    
    // MARK: - Logs
    
    private var logSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Copy All button when logs exist
            if !logs.isEmpty {
                HStack {
                    Spacer()
                    Button {
                        let allText = logs.joined(separator: "\n")
                        NSPasteboard.general.clearContents()
                        NSPasteboard.general.setString(allText, forType: .string)
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "doc.on.doc")
                                .font(.system(size: 9))
                            Text("Copy All")
                                .font(.system(size: 9))
                        }
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.blue)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                }
            }
            
            if logs.isEmpty {
                Text("Ready.")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary.opacity(0.5))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollViewReader { proxy in
                    ScrollView {
                        VStack(alignment: .leading, spacing: 1) {
                            ForEach(Array(logs.enumerated()), id: \.offset) { idx, log in
                                Text(log)
                                    .font(.system(size: 9.5, design: .monospaced))
                                    .foregroundColor(logColor(log))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 1)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .textSelection(.enabled)
                                    .id(idx)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    .onChange(of: logs.count) { _ in
                        if let last = logs.indices.last {
                            withAnimation(.easeOut(duration: 0.15)) {
                                proxy.scrollTo(last, anchor: .bottom)
                            }
                        }
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.black.opacity(0.2))
        .cornerRadius(6)
        .padding(.horizontal, 10)
        .padding(.bottom, 10)
        .padding(.top, 6)
    }
    
    // MARK: - Computed Properties
    
    var isReady: Bool {
        switch mode {
        case .convert: return !paths.isEmpty && !targetFormat.isEmpty
        case .organize: return !paths.isEmpty
        case .summarize: return !paths.isEmpty
        case .rename: return !paths.isEmpty
        case .command: return !customCommand.isEmpty
        }
    }
    
    var actionLabel: String {
        switch mode {
        case .convert: return "Convert"
        case .organize: return "Preview Plan"
        case .summarize: return "Summarize"
        case .rename: return "Preview Renames"
        case .command: return "Run"
        }
    }
    
    var allowedContentTypes: [UTType] {
        switch mode {
        case .organize: return [.folder]
        default: return [.item, .folder]
        }
    }
    
    // MARK: - Actions
    
    func cancelAction() {
        if let p = activeProcess, p.isRunning { p.terminate() }
        DispatchQueue.main.async {
            logs.append("[WARN] Cancelled.")
            isProcessing = false
            activeProcess = nil
        }
    }
    
    func performAction(confirmed: Bool) {
        isProcessing = true
        if !confirmed { logs.removeAll(); hasPlan = false }
        
        let task = Process()
        
        // Use Python directly instead of PyInstaller binary to avoid litellm module issues
        // Get absolute path to Alfred directory
        let alfredDir = "/Users/aryangosaliya/Desktop/Alfred"
        let pythonPath = "\(alfredDir)/cli/venv/bin/python"
        let scriptPath = "\(alfredDir)/cli/alfred.py"
        
        guard FileManager.default.fileExists(atPath: pythonPath) else {
            logs.append("[ERR] Python not found at: \(pythonPath)")
            isProcessing = false
            return
        }
        
        guard FileManager.default.fileExists(atPath: scriptPath) else {
            logs.append("[ERR] Script not found at: \(scriptPath)")
            isProcessing = false
            return
        }
        
        task.executableURL = URL(fileURLWithPath: pythonPath)
        
        var args = [scriptPath]  // Start with script path
        switch mode {
        case .convert:
            args += ["convert", paths[0], targetFormat.trimmingCharacters(in: .whitespaces)]
        case .organize:
            args += ["organize", paths[0]]
            if !organizeInstructions.trimmingCharacters(in: .whitespaces).isEmpty {
                args += ["--instructions", organizeInstructions]
            }
            if confirmed { args += ["--confirm"] }
        case .summarize:
            args += ["summarize"] + paths
        case .rename:
            args += ["rename"] + paths
            if confirmed { args += ["--confirm"] }
        case .command:
            args += ["ask", customCommand] + paths
        }
        
        task.arguments = args
        
        // Environment
        var env = ProcessInfo.processInfo.environment
        let extra = ["/opt/homebrew/bin", "/usr/local/bin", "/opt/homebrew/sbin"]
        let current = env["PATH"] ?? "/usr/bin:/bin"
        let missing = extra.filter { !current.contains($0) }
        if !missing.isEmpty { env["PATH"] = (missing + [current]).joined(separator: ":") }
        task.environment = env
        
        // Set working directory to Alfred/cli
        task.currentDirectoryURL = URL(fileURLWithPath: "\(alfredDir)/cli")
        
        let pipe = Pipe()
        let errPipe = Pipe()
        task.standardOutput = pipe
        task.standardError = errPipe
        activeProcess = task
        
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try task.run()
                let outData = pipe.fileHandleForReading.readDataToEndOfFile()
                let errData = errPipe.fileHandleForReading.readDataToEndOfFile()
                task.waitUntilExit()
                
                DispatchQueue.main.async {
                    if let out = String(data: outData, encoding: .utf8), !out.isEmpty {
                        let lines = out.components(separatedBy: .newlines).filter { !$0.isEmpty }
                        logs.append(contentsOf: lines)
                        
                        // Check for install request
                        for line in lines {
                            if line.contains("[NEED_INSTALL]") {
                                let parts = line.components(separatedBy: "[NEED_INSTALL] ")
                                if parts.count > 1 {
                                    missingTool = parts[1].trimmingCharacters(in: .whitespacesAndNewlines)
                                }
                            }
                        }
                    }
                    if let err = String(data: errData, encoding: .utf8), !err.isEmpty {
                        logs.append(contentsOf: err.components(separatedBy: .newlines).filter { !$0.isEmpty }.map { "[ERR] \($0)" })
                    }
                    
                    let code = task.terminationStatus
                    if code == 0 {
                        // Check if this was a preview
                        let outputText = logs.joined(separator: "\n").lowercased()
                        if !confirmed && (mode == .organize || mode == .rename) {
                            // Check for preview indicators
                            if outputText.contains("preview") || 
                               outputText.contains("plan:") || 
                               outputText.contains("use --confirm") {
                                hasPlan = true
                            }
                        }
                    } else if code != 15 && code != 9 {
                        logs.append("[ERR] Exit code: \(code)")
                    }
                    
                    isProcessing = false
                    activeProcess = nil
                }
            } catch {
                DispatchQueue.main.async {
                    logs.append("[ERR] \(error.localizedDescription)")
                    isProcessing = false
                    activeProcess = nil
                }
            }
        }
    }
    
    func installTool(_ tool: String) {
        missingTool = nil
        isProcessing = true
        logs.append("Installing \(tool)... (this may take a minute)")
        
        let task = Process()
        
        // Use Python directly instead of PyInstaller binary
        let alfredDir = "/Users/aryangosaliya/Desktop/Alfred"
        let pythonPath = "\(alfredDir)/cli/venv/bin/python"
        let scriptPath = "\(alfredDir)/cli/alfred.py"
        
        task.executableURL = URL(fileURLWithPath: pythonPath)
        task.arguments = [scriptPath, "install", tool]
        
        // Environment
        var env = ProcessInfo.processInfo.environment
        task.environment = env
        task.currentDirectoryURL = URL(fileURLWithPath: "\(alfredDir)/cli")
        
        let pipe = Pipe()
        let errPipe = Pipe()
        task.standardOutput = pipe
        task.standardError = errPipe
        
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try task.run()
                // Read continuously for progress updates
                let outHandle = pipe.fileHandleForReading
                let errHandle = errPipe.fileHandleForReading
                
                // For install, we want to see output as it happens (for progress bars if supported, or just text)
                // But CLI Rich output might buffer. We'll read to end for now to keep it simple.
                let outData = outHandle.readDataToEndOfFile()
                let errData = errHandle.readDataToEndOfFile()
                
                task.waitUntilExit()
                
                DispatchQueue.main.async {
                    if let out = String(data: outData, encoding: .utf8) {
                        logs.append(contentsOf: out.components(separatedBy: .newlines).filter { !$0.isEmpty })
                    }
                    if let err = String(data: errData, encoding: .utf8) {
                        logs.append(contentsOf: err.components(separatedBy: .newlines).filter { !$0.isEmpty })
                    }
                    
                    if task.terminationStatus == 0 {
                        logs.append("[SUCCESS] \(tool) installed! You can now retry your task.")
                    } else {
                        logs.append("[ERR] Installation failed.")
                    }
                    isProcessing = false
                }
            } catch {
                DispatchQueue.main.async {
                    logs.append("[ERR] \(error.localizedDescription)")
                    isProcessing = false
                }
            }
        }
    }
    
    // MARK: - Helpers
    
    func logColor(_ log: String) -> Color {
        if log.contains("[ERR]") || log.contains("Error") { return .red }
        if log.contains("Done") || log.contains("Output:") || log.contains("Success") || log.contains("[SUCCESS]") { return .green }
        if log.contains("[WARN]") || log.contains("preview") || log.contains("Skipped") { return .orange }
        if log.contains("[NEED_INSTALL]") { return .yellow }
        if log.starts(with: "  ") && log.contains("->") { return .cyan }
        if log.starts(with: "$") || log.contains("Converting") || log.contains("Summarizing") || log.contains("Analyzing") || log.contains("Installing") { return .blue }
        if log.starts(with: "  ") { return .secondary }
        return .primary
    }
    
    func iconForPath(_ path: String) -> String {
        var isDir: ObjCBool = false
        FileManager.default.fileExists(atPath: path, isDirectory: &isDir)
        if isDir.boolValue { return "folder.fill" }
        let ext = (path as NSString).pathExtension.lowercased()
        switch ext {
        case "json", "csv", "xml", "yaml", "yml": return "doc.text"
        case "png", "jpg", "jpeg", "gif", "webp", "svg": return "photo"
        case "mp4", "avi", "mkv", "mov": return "film"
        case "mp3", "wav", "flac", "aac": return "music.note"
        case "pdf": return "doc.richtext"
        case "py", "swift", "js", "ts", "html": return "chevron.left.forwardslash.chevron.right"
        default: return "doc"
        }
    }
    
    func handleDrop(providers: [NSItemProvider]) {
        let collected = LockedArray()
        let group = DispatchGroup()
        for provider in providers {
            if provider.hasItemConformingToTypeIdentifier("public.file-url") {
                group.enter()
                provider.loadItem(forTypeIdentifier: "public.file-url", options: nil) { item, _ in
                    defer { group.leave() }
                    if let data = item as? Data,
                       let url = URL(dataRepresentation: data, relativeTo: nil) {
                        collected.append(url.path)
                    }
                }
            }
        }
        group.notify(queue: .main) {
            let dropped = collected.values
            if mode == .organize || mode == .convert {
                if let first = dropped.first { paths = [first] }
            } else {
                let existing = Set(paths)
                paths.append(contentsOf: dropped.filter { !existing.contains($0) })
            }
            hasPlan = false
            logs.removeAll()
            missingTool = nil
        }
    }
}

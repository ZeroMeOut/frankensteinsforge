# Design Document: Mobile Responsive Enhancement

## Overview

This design enhances Frankenstein's Forge with comprehensive mobile responsiveness, building upon the existing mobile CSS foundation. The design focuses on touch interactions, adaptive layouts, and optimized user experience across all mobile devices, screen sizes, and orientations. The implementation will refine existing mobile styles, add touch event handling to JavaScript, and ensure all UI components work seamlessly on touchscreen devices.

## Architecture

### Current Architecture
The application currently has:
- Desktop-first CSS in `style-nodes.css`
- Mobile overrides in `style-nodes-mobile.css`
- JavaScript with mouse event handlers in `script-nodes.js`
- HTML with basic viewport meta tags

### Enhanced Architecture
The mobile-responsive enhancement will:
- **Refine CSS**: Improve existing mobile styles with better touch targets, spacing, and responsive patterns
- **Add Touch Support**: Implement touch event handlers alongside existing mouse events
- **Optimize Layouts**: Enhance responsive breakpoints and orientation handling
- **Improve Modals**: Refine modal behavior for mobile with bottom sheet patterns
- **Add Safe Area Support**: Implement proper handling of device notches and safe areas

### Component Interaction Flow

```
User Touch Input
    ↓
Touch Event Handler (JavaScript)
    ↓
Node Graph State Update
    ↓
DOM Manipulation & Canvas Redraw
    ↓
CSS Responsive Styles Applied
    ↓
Visual Feedback to User
```

## Components and Interfaces

### 1. Touch Event Handler Module

**Purpose**: Manage touch interactions for node manipulation and canvas interactions

**Key Functions**:
- `handleTouchStart(event)`: Initialize touch tracking for node drag or selection
- `handleTouchMove(event)`: Update node position during drag
- `handleTouchEnd(event)`: Finalize touch interaction and trigger appropriate actions
- `preventDefaultTouchBehaviors()`: Disable unwanted touch behaviors like zoom and pull-to-refresh

**Integration Points**:
- Extends existing `NodeGraph` class
- Works alongside existing mouse event handlers
- Updates canvas and DOM in real-time

### 2. Responsive Layout Manager

**Purpose**: Handle layout adaptations based on viewport size and orientation

**Key Functions**:
- `detectViewportSize()`: Determine current breakpoint (mobile, tablet, desktop)
- `handleOrientationChange()`: Adjust layout when device orientation changes
- `adjustCanvasSize()`: Resize canvas and reposition nodes proportionally
- `updateLayoutMode()`: Switch between portrait and landscape layouts

**CSS Breakpoints**:
- `< 360px`: Very small mobile devices
- `< 480px`: Small mobile devices
- `< 768px`: Standard mobile devices (portrait)
- `< 896px landscape`: Mobile devices (landscape)
- `< 1024px`: Tablets

### 3. Modal Manager Enhancement

**Purpose**: Optimize modal behavior for mobile devices

**Key Functions**:
- `openModalMobile(modalId)`: Display modal as bottom sheet on mobile
- `closeModalMobile(modalId)`: Dismiss modal with slide-down animation
- `adjustModalHeight()`: Ensure modal respects safe areas and keyboard
- `enableTouchScrolling()`: Enable momentum scrolling within modals

**Behavior**:
- Desktop: Center modal with backdrop
- Mobile: Bottom sheet sliding from bottom
- Keyboard handling: Adjust modal height when keyboard appears

### 4. Touch Target Optimizer

**Purpose**: Ensure all interactive elements meet minimum touch target requirements

**Implementation**:
- Minimum 44x44px touch targets for all buttons
- Adequate spacing between interactive elements
- Visual feedback on touch (active states)
- Prevention of double-tap zoom on buttons

### 5. Safe Area Handler

**Purpose**: Respect device safe areas (notches, home indicators)

**Key Functions**:
- `applySafeAreaInsets()`: Add padding for safe areas
- `detectSafeAreaSupport()`: Check if device has safe areas
- `updateForSafeAreas()`: Adjust layout elements

**CSS Implementation**:
```css
@supports (padding: env(safe-area-inset-bottom)) {
  .generate-section {
    padding-bottom: calc(16px + env(safe-area-inset-bottom));
  }
}
```

## Data Models

### Touch State Model

```javascript
{
  touchId: number,           // Unique touch identifier
  startX: number,            // Initial touch X coordinate
  startY: number,            // Initial touch Y coordinate
  currentX: number,          // Current touch X coordinate
  currentY: number,          // Current touch Y coordinate
  targetNode: Node | null,   // Node being touched
  isDragging: boolean,       // Whether touch is a drag operation
  timestamp: number          // Touch start timestamp
}
```

### Viewport State Model

```javascript
{
  width: number,             // Current viewport width
  height: number,            // Current viewport height
  orientation: 'portrait' | 'landscape',
  breakpoint: 'mobile-xs' | 'mobile-sm' | 'mobile' | 'tablet' | 'desktop',
  hasSafeArea: boolean,      // Device has notch/safe areas
  safeAreaInsets: {
    top: number,
    right: number,
    bottom: number,
    left: number
  }
}
```

### Node Position Model (Enhanced)

```javascript
{
  id: number,
  type: 'text' | 'image' | 'audio',
  x: number,                 // Absolute X position
  y: number,                 // Absolute Y position
  relativeX: number,         // Relative X (0-1) for responsive scaling
  relativeY: number,         // Relative Y (0-1) for responsive scaling
  data: any,
  element: HTMLElement
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Mobile layout structure
*For any* viewport width less than 768 pixels, the app container should display as a single-column flex layout with the graph panel above the results panel
**Validates: Requirements 1.1**

### Property 2: Panel height allocation on mobile
*For any* viewport width less than 768 pixels, the graph panel should occupy 65% of the viewport height and the results panel should occupy 35%
**Validates: Requirements 1.2**

### Property 3: Landscape layout switch
*For any* orientation change to landscape on mobile devices, the layout should switch to a side-by-side configuration with the graph panel occupying 65% of the viewport width
**Validates: Requirements 1.3**

### Property 4: Responsive typography and spacing
*For any* viewport width less than 480 pixels, font sizes and padding values should be reduced compared to larger viewports
**Validates: Requirements 1.4**

### Property 5: Touch target minimum size
*For any* interactive button element on a touch device, the computed width and height should both be at least 44 pixels
**Validates: Requirements 3.1, 3.3**

### Property 6: Node tap selection
*For any* node, when a tap event occurs on that node without dragging, the node should be selected for connection mode
**Validates: Requirements 2.1**

### Property 7: Node drag position update
*For any* node, when a touchmove event occurs during a drag operation, the node position should update to follow the touch coordinates
**Validates: Requirements 2.2**

### Property 8: Connection creation via sequential taps
*For any* two distinct nodes, when a user taps the first node then taps the second node, a connection should be created between them
**Validates: Requirements 2.3**

### Property 9: Connection midpoint tap detection
*For any* connection, when a tap occurs within 20 pixels of the connection midpoint, the weight editor modal should open
**Validates: Requirements 2.4**

### Property 10: Long press context menu prevention
*For any* interactive element, when a long press event occurs, the default context menu should be prevented via preventDefault
**Validates: Requirements 2.5**

### Property 11: Touch interaction visual feedback
*For any* interactive element, when a touch event occurs, the element should apply active state CSS classes and prevent text selection during drag
**Validates: Requirements 2.6, 3.5, 8.5**

### Property 12: Control button grid layout
*For any* viewport width less than 768 pixels, control buttons should be arranged in a CSS grid with adequate gap spacing
**Validates: Requirements 3.2**

### Property 13: Modal button vertical stacking
*For any* modal action buttons on viewports less than 768 pixels wide, the buttons should be stacked vertically with full width
**Validates: Requirements 3.4**

### Property 14: Modal bottom sheet presentation
*For any* modal opened on a viewport less than 768 pixels wide, the modal should be positioned at the bottom with a slide-up animation
**Validates: Requirements 4.1**

### Property 15: Modal maximum height constraint
*For any* modal displayed on mobile, the maximum height should be 85% of the dynamic viewport height
**Validates: Requirements 4.2**

### Property 16: Input font size zoom prevention
*For any* text input or textarea element, the font size should be at least 16 pixels to prevent automatic zoom on iOS
**Validates: Requirements 4.3, 6.1**

### Property 17: Touch scrolling momentum
*For any* scrollable container on mobile, the CSS property -webkit-overflow-scrolling should be set to touch for momentum scrolling
**Validates: Requirements 4.4, 7.2**

### Property 18: Modal dismissal animation
*For any* modal, when the close button is clicked or backdrop is tapped, the modal should dismiss with a smooth animation
**Validates: Requirements 4.5**

### Property 19: Canvas touch behavior prevention
*For any* touch event on the canvas element, default behaviors should be prevented and touch-action CSS should be set to none
**Validates: Requirements 5.1, 10.3**

### Property 20: Real-time connection updates during drag
*For any* node being dragged, the canvas should redraw connections on each position update to maintain visual accuracy
**Validates: Requirements 5.2**

### Property 21: Canvas background tap deselection
*For any* tap event on the canvas that does not hit a node, all currently selected nodes should be deselected
**Validates: Requirements 5.3**

### Property 22: Node boundary constraint during drag
*For any* node being dragged, the final position should be clamped to remain within canvas boundaries (0 to canvas width/height)
**Validates: Requirements 5.4**

### Property 23: Canvas resize and redraw
*For any* canvas resize event due to orientation change, all connections should be redrawn and node positions should be maintained proportionally
**Validates: Requirements 5.5**

### Property 24: Character count indicator display
*For any* text input with a character limit, a character count indicator should be visible and update as the user types
**Validates: Requirements 6.2**

### Property 25: File button full width on mobile
*For any* file upload button on viewports less than 768 pixels wide, the button should have 100% width and meet minimum touch target size
**Validates: Requirements 6.3**

### Property 26: Audio controls vertical layout
*For any* audio recording interface on mobile, the controls should be arranged in a vertical flex layout
**Validates: Requirements 6.4**

### Property 27: Form input type attributes
*For any* form input element, the input should have an appropriate type attribute for mobile keyboard optimization
**Validates: Requirements 6.5**

### Property 28: Result card mobile styling
*For any* result card on viewports less than 768 pixels wide, padding and font sizes should be optimized for mobile readability
**Validates: Requirements 7.1**

### Property 29: Result button horizontal layout
*For any* result action buttons, they should be arranged horizontally with equal flex distribution
**Validates: Requirements 7.3**

### Property 30: Result text formatting
*For any* result card text content, line height should be set to at least 1.6 for comfortable mobile reading
**Validates: Requirements 7.4**

### Property 31: Results header sticky positioning
*For any* results panel, the header should have position: sticky to remain visible during scrolling
**Validates: Requirements 7.5**

### Property 32: Reduced motion animation duration
*For any* user with prefers-reduced-motion enabled, all animations and transitions should have duration less than 0.01 seconds
**Validates: Requirements 8.1**

### Property 33: High DPI border scaling
*For any* device with pixel ratio >= 2, border widths should be adjusted via media query for crisp rendering
**Validates: Requirements 8.2**

### Property 34: Focus indicator visibility
*For any* interactive element when focused, a visible focus outline or indicator should be present
**Validates: Requirements 8.3**

### Property 35: Tap highlight color
*For any* interactive element, the -webkit-tap-highlight-color should be set to a theme-appropriate color
**Validates: Requirements 8.4**

### Property 36: Safe area inset padding
*For any* fixed or sticky element on devices with safe area insets, padding should include env(safe-area-inset-bottom) in calculations
**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

### Property 37: Body overscroll prevention
*For any* scroll event on the body element on mobile, overscroll-behavior should be set to none to prevent bounce effects
**Validates: Requirements 10.1**

### Property 38: Drag scroll prevention
*For any* touchmove event during node drag, preventDefault should be called to prevent page scrolling
**Validates: Requirements 10.2**

### Property 39: Scroll containment
*For any* scrollable container, overscroll-behavior should be set to contain to prevent scroll chaining to parent elements
**Validates: Requirements 10.4**

### Property 40: Body fixed positioning on mobile
*For any* mobile viewport (width < 768px), the body element should have position: fixed to prevent unwanted viewport movement
**Validates: Requirements 10.5**

## Error Handling

### Touch Event Errors

**Scenario**: Touch events fail or are not supported
- **Detection**: Check for `'ontouchstart' in window`
- **Fallback**: Continue using mouse events
- **User Feedback**: No explicit feedback needed (graceful degradation)

### Viewport Detection Errors

**Scenario**: Unable to detect viewport size or orientation
- **Detection**: Check if `window.innerWidth` and `window.innerHeight` are available
- **Fallback**: Use default desktop layout
- **Recovery**: Retry on window resize event

### Canvas Resize Errors

**Scenario**: Canvas fails to resize or redraw
- **Detection**: Monitor canvas dimensions after resize
- **Recovery**: Force canvas redraw with `requestAnimationFrame`
- **User Feedback**: Log error to console, attempt recovery

### Safe Area Detection Errors

**Scenario**: Safe area environment variables not supported
- **Detection**: Use `@supports` CSS query
- **Fallback**: Use standard padding without safe area adjustments
- **Impact**: Minor - content may be slightly closer to edges

### Modal Keyboard Conflicts

**Scenario**: Mobile keyboard obscures modal content
- **Detection**: Monitor `window.visualViewport` changes
- **Recovery**: Adjust modal height or scroll to focused input
- **User Feedback**: Smooth transition to adjusted layout

### Touch State Corruption

**Scenario**: Touch tracking state becomes inconsistent
- **Detection**: Validate touch state on each event
- **Recovery**: Reset touch state on `touchcancel` or `touchend`
- **Prevention**: Always clean up touch listeners

## Testing Strategy

### Unit Testing

**Focus Areas**:
1. Touch event handler functions
2. Viewport detection logic
3. Safe area calculation functions
4. Layout mode switching logic
5. Touch target size validation

**Example Tests**:
- Test that `handleTouchStart` correctly identifies touched node
- Test that `detectViewportSize` returns correct breakpoint
- Test that `applySafeAreaInsets` calculates correct padding
- Test that touch target validation rejects elements < 44px

### Property-Based Testing

**Framework**: Hypothesis (Python) for backend, fast-check (JavaScript) for frontend

**Configuration**: Minimum 100 iterations per property test

**Property Tests** (each tagged with property number):
1. Touch target size validation across random elements
2. Layout adaptation across random viewport sizes
3. Touch event handling across random node positions
4. Connection creation across random node pairs
5. Modal display across random viewport sizes
6. Input font size validation across random inputs
7. Canvas touch behavior across random touch events
8. Node boundary constraints across random drag operations
9. Safe area inset calculations across random inset values
10. Animation duration validation with reduced motion
11. Orientation change handling across random orientations
12. Scroll momentum validation across random containers
13. Visual feedback validation across random interactions
14. Overscroll prevention across random scroll events
15. Connection tap target validation across random connections

### Integration Testing

**Scenarios**:
1. Complete user flow: Add node → Edit content → Connect nodes → Generate idea (mobile)
2. Orientation change during node editing
3. Modal interaction with keyboard appearance
4. Multi-touch gesture handling
5. Rapid touch interactions (stress test)
6. Layout adaptation across all breakpoints
7. Safe area handling on various device types

### Manual Testing Checklist

**Devices**:
- iPhone SE (small screen)
- iPhone 14 Pro (notch)
- iPhone 14 Pro Max (large screen)
- iPad (tablet)
- Android phone (various sizes)
- Android tablet

**Test Cases**:
- [ ] All buttons are easily tappable
- [ ] Nodes can be dragged smoothly
- [ ] Connections can be created via tap
- [ ] Modals display correctly
- [ ] Keyboard doesn't obscure inputs
- [ ] Orientation changes work smoothly
- [ ] No horizontal scrolling occurs
- [ ] Safe areas are respected
- [ ] Scrolling is smooth with momentum
- [ ] No unwanted zoom or pull-to-refresh

### Accessibility Testing

**Tools**: 
- Chrome DevTools Lighthouse
- axe DevTools
- Manual testing with screen readers

**Checks**:
- Touch target sizes meet WCAG 2.1 Level AAA (44x44px)
- Reduced motion preferences respected
- Focus indicators visible
- Color contrast maintained on mobile
- Screen reader compatibility

## Implementation Notes

### CSS Strategy

1. **Mobile-First Approach**: Base styles assume mobile, enhance for desktop
2. **Progressive Enhancement**: Use `@supports` for modern features
3. **Logical Properties**: Use logical properties where appropriate for RTL support
4. **CSS Variables**: Use custom properties for consistent spacing and sizing

### JavaScript Strategy

1. **Event Delegation**: Use event delegation for better performance
2. **Passive Listeners**: Use passive event listeners where appropriate
3. **RequestAnimationFrame**: Use RAF for smooth animations and updates
4. **Debouncing**: Debounce resize and orientation change handlers

### Performance Considerations

1. **Touch Event Throttling**: Throttle touch move events to 60fps
2. **Canvas Optimization**: Only redraw canvas when necessary
3. **DOM Manipulation**: Batch DOM updates to minimize reflows
4. **Image Optimization**: Lazy load images in results panel
5. **CSS Containment**: Use `contain` property for isolated components

### Browser Compatibility

**Target Browsers**:
- iOS Safari 14+
- Chrome Mobile 90+
- Firefox Mobile 90+
- Samsung Internet 14+

**Polyfills Needed**:
- None (using only well-supported features)

**Fallbacks**:
- Touch events → Mouse events
- Dynamic viewport units → Standard viewport units
- Safe area insets → Standard padding

### Deployment Considerations

1. **Testing**: Test on real devices before deployment
2. **Monitoring**: Add analytics for mobile usage patterns
3. **Performance**: Monitor mobile performance metrics
4. **Feedback**: Collect user feedback on mobile experience
5. **Iteration**: Plan for iterative improvements based on usage data

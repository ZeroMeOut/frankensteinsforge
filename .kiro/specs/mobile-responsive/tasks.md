# Implementation Plan

- [x] 1. Audit and refine existing mobile CSS
  - Review current mobile styles in `style-nodes-mobile.css`
  - Identify gaps and inconsistencies with requirements
  - Update breakpoints and media queries for better coverage
  - Ensure all touch target sizes meet 44x44px minimum
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.1, 3.2, 3.3, 3.4_

- [x] 1.1 Write property test for touch target sizes
  - **Property 5: Touch target minimum size**
  - **Validates: Requirements 3.1, 3.3**

- [-] 2. Implement responsive layout improvements
- [x] 2.1 Update mobile portrait layout (< 768px)
  - Ensure single-column flex layout with proper height allocation
  - Set graph panel to 65vh/65dvh and results panel to 35vh/35dvh
  - Fix any overflow or scrolling issues
  - _Requirements: 1.1, 1.2_

- [ ] 2.2 Write property test for mobile layout structure
  - **Property 1: Mobile layout structure**
  - **Validates: Requirements 1.1**

- [ ] 2.3 Write property test for panel height allocation
  - **Property 2: Panel height allocation on mobile**
  - **Validates: Requirements 1.2**

- [x] 2.4 Update landscape layout (< 896px landscape)
  - Implement side-by-side layout with 65/35 width split
  - Ensure proper border and spacing
  - Test orientation change transitions
  - _Requirements: 1.3_

- [ ] 2.5 Write property test for landscape layout
  - **Property 3: Landscape layout switch**
  - **Validates: Requirements 1.3**

- [x] 2.6 Optimize small screen layouts (< 480px)
  - Reduce font sizes and padding appropriately
  - Ensure readability is maintained
  - Test on small devices
  - _Requirements: 1.4_

- [x] 2.7 Write property test for responsive typography
  - **Property 4: Responsive typography and spacing**
  - **Validates: Requirements 1.4**

- [x] 3. Add touch event handling to JavaScript
- [x] 3.1 Implement touch event handlers for nodes
  - Add touchstart, touchmove, touchend listeners to nodes
  - Implement touch-based node selection
  - Implement touch-based node dragging
  - Ensure touch and mouse events work together
  - _Requirements: 2.1, 2.2_

- [x] 3.2 Write property test for node tap selection
  - **Property 6: Node tap selection**
  - **Validates: Requirements 2.1**

- [x] 3.3 Write property test for node drag position update
  - **Property 7: Node drag position update**
  - **Validates: Requirements 2.2**

- [x] 3.4 Implement connection creation via touch
  - Handle sequential node taps for connection creation
  - Update mode indicator text appropriately
  - Ensure visual feedback during connection mode
  - _Requirements: 2.3_

- [x] 3.5 Write property test for connection creation
  - **Property 8: Connection creation via sequential taps**
  - **Validates: Requirements 2.3**

- [x] 3.6 Implement connection weight editing via touch
  - Add touch detection for connection midpoints
  - Ensure tap target is at least 30px radius
  - Open weight modal on connection tap
  - _Requirements: 2.4_

- [x] 3.7 Write property test for connection tap detection
  - **Property 9: Connection midpoint tap detection**
  - **Validates: Requirements 2.4**

- [x] 3.8 Add long press prevention
  - Prevent context menu on long press
  - Add contextmenu event listener with preventDefault
  - Test on iOS and Android
  - _Requirements: 2.5_

- [x] 3.9 Write property test for long press prevention
  - **Property 10: Long press context menu prevention**
  - **Validates: Requirements 2.5**

- [x] 3.10 Implement visual feedback for touch interactions
  - Add active state classes on touch
  - Prevent text selection during drag
  - Add CSS for touch feedback
  - _Requirements: 2.6, 3.5, 8.5_

- [x] 3.11 Write property test for touch visual feedback
  - **Property 11: Touch interaction visual feedback**
  - **Validates: Requirements 2.6, 3.5, 8.5**

- [x] 4. Enhance modal behavior for mobile
- [x] 4.1 Implement bottom sheet modal presentation
  - Update modal CSS for mobile bottom sheet style
  - Add slide-up animation from bottom
  - Ensure backdrop blur effect
  - _Requirements: 4.1_

- [x] 4.2 Write property test for modal presentation
  - **Property 14: Modal bottom sheet presentation**
  - **Validates: Requirements 4.1**

- [x] 4.3 Set modal maximum height constraints
  - Use 85dvh for modal max-height on mobile
  - Ensure modal content is scrollable when needed
  - Test with keyboard appearance
  - _Requirements: 4.2_

- [x] 4.4 Write property test for modal height
  - **Property 15: Modal maximum height constraint**
  - **Validates: Requirements 4.2**

- [x] 4.5 Optimize form inputs for mobile
  - Set all input/textarea font-size to 16px minimum
  - Add appropriate input type attributes
  - Ensure proper keyboard types appear
  - _Requirements: 4.3, 6.1, 6.5_

- [x] 4.6 Write property test for input font size
  - **Property 16: Input font size zoom prevention**
  - **Validates: Requirements 4.3, 6.1**

- [x] 4.7 Write property test for input type attributes
  - **Property 27: Form input type attributes**
  - **Validates: Requirements 6.5**

- [x] 4.8 Enable touch scrolling momentum
  - Add -webkit-overflow-scrolling: touch to scrollable containers
  - Add overscroll-behavior: contain
  - Test smooth scrolling on iOS
  - _Requirements: 4.4, 7.2_

- [x] 4.9 Write property test for touch scrolling
  - **Property 17: Touch scrolling momentum**
  - **Validates: Requirements 4.4, 7.2**

- [x] 4.10 Implement modal dismissal with animation
  - Ensure smooth close animation
  - Handle backdrop tap dismissal
  - Handle close button tap dismissal
  - _Requirements: 4.5_

- [x] 4.11 Write property test for modal dismissal
  - **Property 18: Modal dismissal animation**
  - **Validates: Requirements 4.5**

- [-] 5. Optimize canvas for touch interactions
- [x] 5.1 Prevent default canvas touch behaviors
  - Set touch-action: none on canvas
  - Call preventDefault on touch events
  - Disable pinch-zoom and pull-to-refresh
  - _Requirements: 5.1, 10.3_

- [x] 5.2 Write property test for canvas touch prevention
  - **Property 19: Canvas touch behavior prevention**
  - **Validates: Requirements 5.1, 10.3**

- [ ] 5.3 Implement real-time connection updates
  - Redraw canvas on every touchmove during drag
  - Use requestAnimationFrame for smooth updates
  - Optimize redraw performance
  - _Requirements: 5.2_

- [ ] 5.4 Write property test for connection updates
  - **Property 20: Real-time connection updates during drag**
  - **Validates: Requirements 5.2**

- [ ] 5.5 Add canvas background tap handling
  - Detect taps on empty canvas areas
  - Deselect all nodes on background tap
  - Update mode indicator
  - _Requirements: 5.3_

- [ ] 5.6 Write property test for background tap
  - **Property 21: Canvas background tap deselection**
  - **Validates: Requirements 5.3**

- [ ] 5.7 Implement node boundary constraints
  - Clamp node positions to canvas boundaries during drag
  - Account for node dimensions in boundary calculation
  - Test with various canvas sizes
  - _Requirements: 5.4_

- [ ] 5.8 Write property test for boundary constraints
  - **Property 22: Node boundary constraint during drag**
  - **Validates: Requirements 5.4**

- [ ] 5.9 Handle canvas resize and orientation changes
  - Redraw connections on resize
  - Maintain node positions proportionally
  - Test orientation change transitions
  - _Requirements: 5.5_

- [ ] 5.10 Write property test for canvas resize
  - **Property 23: Canvas resize and redraw**
  - **Validates: Requirements 5.5**

- [x] 6. Enhance mobile UI components
- [x] 6.1 Update control buttons layout
  - Implement CSS grid for control buttons on mobile
  - Ensure adequate gap spacing (8px minimum)
  - Make clear button full-width
  - _Requirements: 3.2_

- [x] 6.2 Write property test for control button layout
  - **Property 12: Control button grid layout**
  - **Validates: Requirements 3.2**

- [x] 6.3 Update modal action buttons
  - Stack buttons vertically on mobile
  - Set full width for each button
  - Ensure proper spacing between buttons
  - _Requirements: 3.4_

- [x] 6.4 Write property test for modal button layout
  - **Property 13: Modal button vertical stacking**
  - **Validates: Requirements 3.4**

- [x] 6.5 Add character count indicators
  - Display character count for text inputs
  - Update count in real-time as user types
  - Show count in format "X / MAX"
  - _Requirements: 6.2_

- [x] 6.6 Write property test for character count
  - **Property 24: Character count indicator display**
  - **Validates: Requirements 6.2**

- [x] 6.7 Optimize file upload buttons
  - Make file buttons full-width on mobile
  - Ensure minimum 52px height
  - Add proper touch feedback
  - _Requirements: 6.3_

- [x] 6.8 Write property test for file button sizing
  - **Property 25: File button full width on mobile**
  - **Validates: Requirements 6.3**

- [x] 6.9 Update audio recording interface
  - Stack audio controls vertically on mobile
  - Ensure buttons are full-width
  - Test recording functionality on mobile
  - _Requirements: 6.4_

- [x] 6.10 Write property test for audio controls layout
  - **Property 26: Audio controls vertical layout**
  - **Validates: Requirements 6.4**

- [x] 7. Optimize results panel for mobile
- [x] 7.1 Update result card styling
  - Adjust padding for mobile (16px)
  - Optimize font sizes for readability
  - Ensure proper line height (1.6+)
  - _Requirements: 7.1, 7.4_

- [x] 7.2 Write property test for result card styling
  - **Property 28: Result card mobile styling**
  - **Validates: Requirements 7.1**

- [x] 7.3 Write property test for result text formatting
  - **Property 30: Result text formatting**
  - **Validates: Requirements 7.4**

- [x] 7.4 Update result action buttons
  - Arrange buttons horizontally with flex
  - Set equal width distribution (flex: 1)
  - Ensure minimum touch target size
  - _Requirements: 7.3_

- [x] 7.5 Write property test for result button layout
  - **Property 29: Result button horizontal layout**
  - **Validates: Requirements 7.3**

- [x] 7.6 Make results header sticky
  - Set position: sticky on results header
  - Set top: 0 for sticky positioning
  - Add background color to prevent transparency
  - _Requirements: 7.5_

- [x] 7.7 Write property test for sticky header
  - **Property 31: Results header sticky positioning**
  - **Validates: Requirements 7.5**

- [x] 8. Implement accessibility and device-specific features
- [x] 8.1 Add reduced motion support
  - Create @media (prefers-reduced-motion: reduce) query
  - Set animation-duration to 0.01ms for all elements
  - Set transition-duration to 0.01ms for all elements
  - _Requirements: 8.1_

- [x] 8.2 Write property test for reduced motion
  - **Property 32: Reduced motion animation duration**
  - **Validates: Requirements 8.1**

- [x] 8.3 Optimize for high DPI displays
  - Add @media (-webkit-min-device-pixel-ratio: 2) query
  - Adjust border widths for retina displays
  - Test on high DPI devices
  - _Requirements: 8.2_

- [x] 8.4 Write property test for high DPI borders
  - **Property 33: High DPI border scaling**
  - **Validates: Requirements 8.2**

- [x] 8.5 Ensure focus indicators are visible
  - Add visible focus styles to all interactive elements
  - Use outline or box-shadow for focus indication
  - Test keyboard navigation
  - _Requirements: 8.3_

- [x] 8.6 Write property test for focus indicators
  - **Property 34: Focus indicator visibility**
  - **Validates: Requirements 8.3**

- [x] 8.7 Set tap highlight color
  - Set -webkit-tap-highlight-color to theme color
  - Use rgba(74, 222, 128, 0.15) for consistency
  - Test on iOS devices
  - _Requirements: 8.4_

- [x] 8.8 Write property test for tap highlight
  - **Property 35: Tap highlight color**
  - **Validates: Requirements 8.4**

- [x] 9. Implement safe area support
- [x] 9.1 Add safe area inset handling
  - Create @supports (padding: env(safe-area-inset-bottom)) query
  - Add safe area padding to generate button
  - Add safe area padding to results container
  - Add safe area padding to modals
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 9.2 Write property test for safe area insets
  - **Property 36: Safe area inset padding**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [x] 10. Prevent unwanted scroll behaviors
- [x] 10.1 Prevent body overscroll
  - Set overscroll-behavior: none on body for mobile
  - Set position: fixed on body for mobile
  - Ensure app container fills viewport
  - _Requirements: 10.1, 10.5_

- [x] 10.2 Write property test for body overscroll
  - **Property 37: Body overscroll prevention**
  - **Validates: Requirements 10.1**

- [x] 10.3 Write property test for body positioning
  - **Property 40: Body fixed positioning on mobile**
  - **Validates: Requirements 10.5**

- [x] 10.4 Prevent scroll during drag
  - Call preventDefault on touchmove during node drag
  - Ensure page doesn't scroll when dragging nodes
  - Test on iOS and Android
  - _Requirements: 10.2_

- [x] 10.5 Write property test for drag scroll prevention
  - **Property 38: Drag scroll prevention**
  - **Validates: Requirements 10.2**

- [x] 10.6 Implement scroll containment
  - Set overscroll-behavior: contain on scrollable containers
  - Prevent scroll chaining to parent elements
  - Test nested scrolling behavior
  - _Requirements: 10.4_

- [x] 10.7 Write property test for scroll containment
  - **Property 39: Scroll containment**
  - **Validates: Requirements 10.4**

- [x] 11. Testing and refinement
- [x] 11.1 Test on real mobile devices
  - Test on iPhone (various models)
  - Test on Android devices (various sizes)
  - Test on iPad/tablets
  - Document any device-specific issues
  - _Requirements: All_

- [x] 11.2 Test orientation changes
  - Test portrait to landscape transitions
  - Test landscape to portrait transitions
  - Ensure smooth transitions and no layout breaks
  - _Requirements: 1.3, 5.5_

- [x] 11.3 Test touch interactions comprehensively
  - Test node dragging on various devices
  - Test connection creation flow
  - Test modal interactions
  - Test all button taps
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 11.4 Verify accessibility compliance
  - Run Lighthouse accessibility audit
  - Test with screen readers
  - Verify WCAG 2.1 Level AAA touch target compliance
  - Test keyboard navigation
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

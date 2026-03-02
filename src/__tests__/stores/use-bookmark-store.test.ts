import { useBookmarkStore } from '@/stores/use-bookmark-store'

describe('useBookmarkStore', () => {
  beforeEach(() => {
    useBookmarkStore.setState({ bookmarks: {} })
  })

  describe('toggleBookmark', () => {
    it('adds a bookmark when not bookmarked', () => {
      useBookmarkStore.getState().toggleBookmark('q_001')

      expect(useBookmarkStore.getState().bookmarks).toEqual({ q_001: true })
    })

    it('removes a bookmark when already bookmarked', () => {
      useBookmarkStore.getState().toggleBookmark('q_001')
      useBookmarkStore.getState().toggleBookmark('q_001')

      expect(useBookmarkStore.getState().bookmarks).toEqual({})
    })

    it('handles multiple bookmarks independently', () => {
      useBookmarkStore.getState().toggleBookmark('q_001')
      useBookmarkStore.getState().toggleBookmark('q_002')

      expect(useBookmarkStore.getState().bookmarks).toEqual({
        q_001: true,
        q_002: true,
      })
    })
  })

  describe('isBookmarked', () => {
    it('returns true for bookmarked question', () => {
      useBookmarkStore.getState().toggleBookmark('q_001')

      expect(useBookmarkStore.getState().isBookmarked('q_001')).toBe(true)
    })

    it('returns false for non-bookmarked question', () => {
      expect(useBookmarkStore.getState().isBookmarked('q_999')).toBe(false)
    })
  })

  describe('getBookmarkedIds', () => {
    it('returns empty array when no bookmarks', () => {
      expect(useBookmarkStore.getState().getBookmarkedIds()).toEqual([])
    })

    it('returns all bookmarked question ids', () => {
      useBookmarkStore.getState().toggleBookmark('q_001')
      useBookmarkStore.getState().toggleBookmark('q_002')

      const ids = useBookmarkStore.getState().getBookmarkedIds()
      expect(ids).toHaveLength(2)
      expect(ids).toContain('q_001')
      expect(ids).toContain('q_002')
    })
  })

  describe('clearBookmarks', () => {
    it('removes all bookmarks', () => {
      useBookmarkStore.getState().toggleBookmark('q_001')
      useBookmarkStore.getState().toggleBookmark('q_002')
      useBookmarkStore.getState().clearBookmarks()

      expect(useBookmarkStore.getState().bookmarks).toEqual({})
      expect(useBookmarkStore.getState().getBookmarkedIds()).toEqual([])
    })
  })
})

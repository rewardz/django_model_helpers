from nose import tools
from time import sleep
from sample.models import Team


def test_cached_property():

    team1 = Team.objects.create(name="Team1")
    team2 = Team.objects.create(name="Team2")
    # Make sure the counter is incrementing
    tools.assert_equal(team1.get_counter(), 1)
    tools.assert_equal(team1.get_counter(), 2)
    tools.assert_equal(team1.get_counter(), 3)
    # Test caching
    tools.assert_equal(team1.cached_counter, 4)
    tools.assert_equal(team1.cached_counter, 4)
    tools.assert_equal(team1.cached_counter, 4)
    # Make sure caching is still working even if I made new instance
    team1_new = Team.objects.get(pk=team1.pk)
    tools.assert_equal(team1_new.cached_counter, 4)
    tools.assert_equal(team1_new.cached_counter, 4)
    # Make sure team2 is not affected by any of this
    team2.get_counter()
    tools.assert_equal(team2.cached_counter, 2)
    tools.assert_equal(team2.cached_counter, 2)
    # Reset caching, let get_counter get called again for both team1 and team1_new
    del team1_new.cached_counter
    tools.assert_equal(team1.cached_counter, 5)
    tools.assert_equal(team1_new.cached_counter, 5)
    del team1_new.cached_counter
    tools.assert_equal(team1_new.cached_counter, 1)
    # team2's caching shouldn't be affected though
    tools.assert_equal(team2.cached_counter, 2)


def test_writeable_cached_property():
    team1 = Team.objects.create(name="Team1")
    team2 = Team.objects.create(name="Team2")

    tools.assert_equal(team1.writable_cached_counter, 1)
    tools.assert_equal(team2.writable_cached_counter, 1)

    team1.writable_cached_counter = 77
    tools.assert_equal(team1.writable_cached_counter, 77)
    tools.assert_equal(Team.objects.get(pk=team1.pk).writable_cached_counter, 77)
    tools.assert_equal(team2.writable_cached_counter, 1)
    tools.assert_equal(Team.objects.get(pk=team2.pk).writable_cached_counter, 1)

    # Removing the cache should remove the weird effect
    del team1.writable_cached_counter
    tools.assert_equal(team1.writable_cached_counter, 2)
    tools.assert_equal(team2.writable_cached_counter, 1)
    del team2.writable_cached_counter
    tools.assert_equal(team2.writable_cached_counter, 2)


def test_cache_timeout():
    team = Team(name="Team1")
    tools.assert_equal(team.one_sec_cache, 1)
    tools.assert_equal(team.one_sec_cache, 1)
    tools.assert_equal(team.one_sec_cache, 1)
    sleep(2)
    tools.assert_equal(team.one_sec_cache, 2)
    tools.assert_equal(team.one_sec_cache, 2)

    # test default cache timeout (we set it to 3 seconds)
    team = Team(name="Team1")
    del team.cached_counter
    tools.assert_equal(team.cached_counter, 1)
    tools.assert_equal(team.cached_counter, 1)
    sleep(4)
    tools.assert_equal(team.cached_counter, 2)
